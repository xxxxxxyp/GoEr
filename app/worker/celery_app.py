from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from celery import Celery, chain
from celery.schedules import crontab
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.subscription import Subscription


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BEAT_SCHEDULE_FILE = PROJECT_ROOT / "celerybeat-schedule"


celery_app = Celery(
    "goer_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    beat_schedule_filename=str(BEAT_SCHEDULE_FILE),
    task_track_started=True,
)


async def _load_active_subscriptions() -> list[Subscription]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Subscription).where(
                Subscription.is_active.is_(True),
                Subscription.cron_schedule.is_not(None),
            ),
        )

        # Filter out empty cron strings that may pass the SQL non-null check.
        return [
            subscription
            for subscription in result.scalars().all()
            if (subscription.cron_schedule or "").strip()
        ]


def _run_async_in_sync_context(coro: Any) -> Any:
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None

    if running_loop and running_loop.is_running():
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    return asyncio.run(coro)


def _cron_from_expr(cron_expr: str):
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {cron_expr}")

    minute, hour, day_of_month, month_of_year, day_of_week = parts
    return crontab(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
    )


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender: Celery, **_: Any) -> None:
    try:
        subscriptions = _run_async_in_sync_context(_load_active_subscriptions())
    except Exception:
        logger.exception("Failed to load subscriptions for dynamic beat scheduling")
        return

    registered = 0
    for subscription in subscriptions:
        cron_expr = (subscription.cron_schedule or "").strip()

        try:
            schedule = _cron_from_expr(cron_expr)
        except ValueError:
            logger.warning(
                "Skipping subscription id=%s due to invalid cron: %s",
                subscription.id,
                cron_expr,
            )
            continue

        search_query = (subscription.search_query or "all").strip() or "all"
        workflow = chain(
            sender.signature(
                "app.worker.tasks.fetch_arxiv_papers",
                kwargs={"search_query": search_query, "max_results": 5},
            ),
            sender.signature("app.worker.tasks.parse_pdf_text"),
            sender.signature("app.worker.tasks.llm_summarize"),
            sender.signature(
                "app.worker.tasks.save_to_database",
                kwargs={
                    "user_id": subscription.user_id,
                    "subscription_id": subscription.id,
                },
            ),
        )

        sender.add_periodic_task(
            schedule,
            workflow,
            name=f"subscription-sync-{subscription.id}",
        )
        registered += 1

    logger.info("Registered %s dynamic subscription beat tasks", registered)
