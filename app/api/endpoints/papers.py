import logging

from celery import chain
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.paper import Paper
from app.models.paper_summary import PaperSummary
from app.models.subscription import Subscription
from app.models.user import User
from app.models.user_paper_interaction import UserPaperInteraction
from app.schemas.paper import MessageResponse, UnreadPaperResponse
from app.worker.tasks import fetch_arxiv_papers, llm_summarize, parse_pdf_text, save_to_database


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/unread", response_model=list[UnreadPaperResponse])
async def get_unread_papers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UnreadPaperResponse]:
    result = await db.execute(
        select(UserPaperInteraction, Paper, PaperSummary)
        .join(Paper, UserPaperInteraction.paper_id == Paper.id)
        .outerjoin(PaperSummary, PaperSummary.paper_id == Paper.id)
        .where(
            UserPaperInteraction.user_id == current_user.id,
            UserPaperInteraction.status == "unread",
        )
        .order_by(UserPaperInteraction.added_at.desc()),
    )

    response: list[UnreadPaperResponse] = []
    for interaction, paper, summary in result.all():
        authors = paper.authors if isinstance(paper.authors, list) else []
        response.append(
            UnreadPaperResponse(
                interaction_id=interaction.id,
                paper_title=paper.title,
                authors=authors,
                core_innovation=summary.core_innovation if summary else None,
                relevance_score=summary.relevance_score if summary else None,
                added_at=interaction.added_at,
            ),
        )

    return response


@router.post("/{interaction_id}/read", response_model=MessageResponse)
async def mark_paper_as_read(
    interaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    result = await db.execute(
        select(UserPaperInteraction).where(
            UserPaperInteraction.id == interaction_id,
            UserPaperInteraction.user_id == current_user.id,
        ),
    )
    interaction = result.scalar_one_or_none()

    if interaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found",
        )

    interaction.status = "read"
    await db.commit()

    return MessageResponse(message="Marked as read")


@router.post("/trigger-fetch", response_model=MessageResponse)
async def trigger_fetch(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    active_subscriptions_result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.is_active.is_(True),
        ),
    )
    active_subscriptions = list(active_subscriptions_result.scalars().all())

    if not active_subscriptions:
        return MessageResponse(message="No active subscriptions found")

    queued_count = 0
    for subscription in active_subscriptions:
        search_query = subscription.search_query or "all"
        workflow = chain(
            fetch_arxiv_papers.s(search_query=search_query, max_results=5),
            parse_pdf_text.s(),
            llm_summarize.s(),
            save_to_database.s(user_id=current_user.id, subscription_id=subscription.id),
        )
        task_result = workflow.apply_async()
        queued_count += 1

        logger.info(
            "Queued celery workflow task_id=%s user_id=%s subscription_id=%s",
            task_result.id,
            current_user.id,
            subscription.id,
        )

    return MessageResponse(message=f"Queued {queued_count} fetch workflows")
