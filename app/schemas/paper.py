from datetime import datetime

from pydantic import BaseModel


class UnreadPaperResponse(BaseModel):
    interaction_id: int
    paper_title: str
    authors: list[str]
    core_innovation: str | None
    relevance_score: float | None
    added_at: datetime


class MessageResponse(BaseModel):
    message: str
