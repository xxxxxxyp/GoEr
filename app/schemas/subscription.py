from pydantic import BaseModel, ConfigDict, Field


class SubscriptionCreate(BaseModel):
    source_platform: str = Field(min_length=1, max_length=50)
    search_query: str = Field(min_length=1, max_length=255)
    cron_schedule: str = Field(min_length=1, max_length=50)


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    source_platform: str | None
    search_query: str | None
    cron_schedule: str | None
    is_active: bool
