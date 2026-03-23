from __future__ import annotations

import sys
import asyncio
import json
import logging
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Any, Coroutine, TypeVar

import httpx
from celery.utils.log import get_task_logger
from sqlalchemy import and_, select

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.paper import Paper
from app.models.paper_summary import PaperSummary
from app.models.user_paper_interaction import UserPaperInteraction
from app.worker.celery_app import celery_app


logger = get_task_logger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

T = TypeVar("T")

QWEN_SYSTEM_PROMPT = (
    "你是一位资深的机器人与 AI 研究专家。"
    "请阅读用户提供的论文摘要，并输出严格 JSON 格式总结。"
    "特别注意：如果论文涉及 '3D 建模'、'超声波感知' 或 '语音防伪'，"
    "请在核心创新点中重点标注其对实际工程的参考价值。"
)


def _text(node: ET.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return " ".join(node.text.split())


def _parse_arxiv_feed(feed_xml: str) -> list[dict[str, Any]]:
    root = ET.fromstring(feed_xml)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    papers: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        raw_id = _text(entry.find("atom:id", ns))
        external_id = raw_id.rsplit("/", maxsplit=1)[-1] if raw_id else ""
        title = _text(entry.find("atom:title", ns))
        summary = _text(entry.find("atom:summary", ns))
        published_date = _text(entry.find("atom:published", ns))

        authors: list[str] = []
        for author in entry.findall("atom:author", ns):
            author_name = _text(author.find("atom:name", ns))
            if author_name:
                authors.append(author_name)

        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            link_href = link.attrib.get("href", "")
            link_title = link.attrib.get("title", "")
            link_type = link.attrib.get("type", "")
            if link_title == "pdf" or link_type == "application/pdf":
                pdf_url = link_href
                break

        papers.append(
            {
                "external_id": external_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "published_date": published_date,
                "pdf_url": pdf_url,
            },
        )

    return papers


def _fallback_llm_summary(full_text: str) -> dict[str, Any]:
    normalized = " ".join(full_text.split())
    preview = normalized[:160] + ("..." if len(normalized) > 160 else "")

    return {
        "core_innovation": (
            f"Fallback: 该工作核心创新可概括为 {preview}" if preview else "Fallback: 暂无可提取的核心创新文本"
        ),
        "methodology": "Fallback: Qwen 调用失败，使用摘要启发式生成。",
        "limitations": "Fallback: 当前结果并非模型标准输出，需后续复核。",
        "relevance_score": 78.5,
        "llm_model": "fallback",
    }


def _extract_json_block(text: str) -> str:
    stripped = text.strip()

    fence_pattern = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.IGNORECASE | re.DOTALL)
    fence_match = fence_pattern.search(stripped)
    if fence_match:
        return fence_match.group(1).strip()

    decoder = json.JSONDecoder()
    for idx, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            _, end = decoder.raw_decode(stripped[idx:])
            return stripped[idx : idx + end]
        except json.JSONDecodeError:
            continue

    return stripped


def _safe_relevance_score(raw_value: Any) -> float:
    try:
        score = float(raw_value)
    except (TypeError, ValueError):
        return 0.0

    return max(0.0, min(100.0, score))


def _normalize_summary_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "core_innovation": str(payload.get("core_innovation") or ""),
        "methodology": str(payload.get("methodology") or ""),
        "limitations": str(payload.get("limitations") or ""),
        "relevance_score": _safe_relevance_score(payload.get("relevance_score")),
        "llm_model": str(payload.get("llm_model") or settings.qwen_model),
    }


def _call_qwen_summary(full_text: str) -> dict[str, Any]:
    if not settings.qwen_api_key:
        raise RuntimeError("QWEN_API_KEY is not configured")

    user_prompt = (
        "请阅读以下论文摘要，并仅返回 JSON 对象，字段必须是："
        "core_innovation, methodology, limitations, relevance_score。\n\n"
        f"论文摘要:\n{full_text}"
    )
    request_url = settings.qwen_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.qwen_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.qwen_model,
        "messages": [
            {"role": "system", "content": QWEN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    with httpx.Client(timeout=settings.qwen_timeout_seconds) as client:
        response = client.post(request_url, headers=headers, json=payload)
        response.raise_for_status()

    body = response.json()
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Qwen response missing choices")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ValueError("Qwen response message is invalid")

    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError("Qwen response content is not text")

    json_text = _extract_json_block(content)
    parsed = json.loads(json_text)
    if not isinstance(parsed, dict):
        raise ValueError("Qwen output JSON is not an object")

    return _normalize_summary_payload(parsed)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None

    date_part = value.split("T", maxsplit=1)[0]
    try:
        return date.fromisoformat(date_part)
    except ValueError:
        return None


def _run_async_in_sync_context(coro: Coroutine[Any, Any, T]) -> T:
    # 针对 Windows 环境的特殊处理
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def _thread_runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_thread_runner)
        return future.result()


async def _save_to_database_async(
    papers_list: list[dict[str, Any]],
    user_id: int,
    subscription_id: int,
) -> dict[str, int]:
    inserted_papers = 0
    upserted_summaries = 0
    created_interactions = 0

    async with AsyncSessionLocal() as db:
        try:
            for paper_data in papers_list:
                external_id = (paper_data.get("external_id") or "").strip()
                title = (paper_data.get("title") or "").strip()

                if not external_id or not title:
                    logger.warning("Skipping invalid paper payload: %s", paper_data)
                    continue

                existing_paper_result = await db.execute(
                    select(Paper).where(Paper.external_id == external_id),
                )
                paper = existing_paper_result.scalar_one_or_none()

                if paper is None:
                    paper = Paper(
                        external_id=external_id,
                        title=title,
                        authors=paper_data.get("authors") or [],
                        abstract_original=paper_data.get("summary") or None,
                        published_date=_parse_date(paper_data.get("published_date")),
                        pdf_url=paper_data.get("pdf_url") or None,
                        is_parsed=bool(paper_data.get("full_text")),
                    )
                    db.add(paper)
                    await db.flush()
                    inserted_papers += 1
                else:
                    paper.title = title or paper.title
                    paper.authors = paper_data.get("authors") or paper.authors
                    paper.abstract_original = paper_data.get("summary") or paper.abstract_original
                    paper.published_date = _parse_date(paper_data.get("published_date")) or paper.published_date
                    paper.pdf_url = paper_data.get("pdf_url") or paper.pdf_url
                    paper.is_parsed = paper.is_parsed or bool(paper_data.get("full_text"))

                summary_payload = paper_data.get("summary_structured") or {}
                if summary_payload:
                    llm_model_name = str(summary_payload.get("llm_model") or settings.qwen_model)
                    relevance_score = _safe_relevance_score(summary_payload.get("relevance_score"))
                    existing_summary_result = await db.execute(
                        select(PaperSummary).where(PaperSummary.paper_id == paper.id),
                    )
                    paper_summary = existing_summary_result.scalar_one_or_none()

                    if paper_summary is None:
                        paper_summary = PaperSummary(
                            paper_id=paper.id,
                            core_innovation=summary_payload.get("core_innovation"),
                            methodology=summary_payload.get("methodology"),
                            limitations=summary_payload.get("limitations"),
                            relevance_score=relevance_score,
                            llm_model=llm_model_name,
                        )
                        db.add(paper_summary)
                    else:
                        paper_summary.core_innovation = summary_payload.get("core_innovation")
                        paper_summary.methodology = summary_payload.get("methodology")
                        paper_summary.limitations = summary_payload.get("limitations")
                        paper_summary.relevance_score = relevance_score
                        paper_summary.llm_model = llm_model_name

                    upserted_summaries += 1

                interaction_result = await db.execute(
                    select(UserPaperInteraction).where(
                        and_(
                            UserPaperInteraction.user_id == user_id,
                            UserPaperInteraction.paper_id == paper.id,
                        ),
                    ),
                )
                interaction = interaction_result.scalar_one_or_none()

                if interaction is None:
                    interaction = UserPaperInteraction(
                        user_id=user_id,
                        paper_id=paper.id,
                        subscription_id=subscription_id,
                        status="unread",
                    )
                    db.add(interaction)
                    created_interactions += 1
                elif interaction.subscription_id is None:
                    interaction.subscription_id = subscription_id

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    return {
        "inserted_papers": inserted_papers,
        "upserted_summaries": upserted_summaries,
        "created_interactions": created_interactions,
    }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_arxiv_papers(
    self,
    search_query: str,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    try:
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        request_url = settings.arxiv_api_url
        if request_url.startswith("http://"):
            request_url = "https://" + request_url[len("http://") :]

        with httpx.Client(timeout=30.0) as client:
            response = client.get(request_url, params=params, follow_redirects=True)
            response.raise_for_status()

        papers = _parse_arxiv_feed(response.text)
        logger.info(
            "Fetched %s papers from arXiv for query=%s",
            len(papers),
            search_query,
        )
        return papers
    except Exception as exc:
        logger.exception("fetch_arxiv_papers failed for query=%s", search_query)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def parse_pdf_text(
    self,
    papers_list: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    try:
        parsed: list[dict[str, Any]] = []
        for paper in papers_list:
            item = dict(paper)
            item["full_text"] = item.get("summary") or ""
            parsed.append(item)

        logger.info("Mock PDF parsing completed for %s papers", len(parsed))
        return parsed
    except Exception as exc:
        logger.exception("parse_pdf_text failed")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def llm_summarize(
    self,
    papers_list: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    try:
        summarized: list[dict[str, Any]] = []
        for paper in papers_list:
            item = dict(paper)
            full_text = item.get("full_text") or ""

            try:
                item["summary_structured"] = _call_qwen_summary(full_text)
            except Exception as exc:
                logger.exception(
                    "Qwen summarize failed for external_id=%s, fallback enabled",
                    item.get("external_id"),
                )
                fallback = _fallback_llm_summary(full_text)
                fallback["limitations"] = (
                    fallback["limitations"] + f" Error: {exc.__class__.__name__}"
                )
                item["summary_structured"] = fallback

            summarized.append(item)

        logger.info("LLM summarize completed for %s papers", len(summarized))
        return summarized
    except Exception as exc:
        logger.exception("llm_summarize failed")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def save_to_database(
    self,
    papers_list: list[dict[str, Any]],
    user_id: int,
    subscription_id: int,
) -> dict[str, int]:
    try:
        stats = _run_async_in_sync_context(
            _save_to_database_async(
                papers_list=papers_list,
                user_id=user_id,
                subscription_id=subscription_id,
            ),
        )
        logger.info(
            "Saved pipeline output for user_id=%s subscription_id=%s stats=%s",
            user_id,
            subscription_id,
            stats,
        )
        return stats
    except Exception as exc:
        logger.exception(
            "save_to_database failed for user_id=%s subscription_id=%s",
            user_id,
            subscription_id,
        )
        raise self.retry(exc=exc)
