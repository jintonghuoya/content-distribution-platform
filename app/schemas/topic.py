import datetime
from typing import Any

from pydantic import BaseModel, Field


class TopicCreate(BaseModel):
    title: str
    source: str
    source_id: str = ""
    source_url: str = ""
    rank: int | None = None
    heat_value: int | None = 0
    raw_data: dict[str, Any] | None = None


class TopicResponse(BaseModel):
    id: int
    title: str
    source: str
    source_id: str
    source_url: str
    rank: int | None
    heat_value: int | None
    category: str | None
    priority: float | None = None
    status: str
    collected_at: datetime.datetime
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class TopicListResponse(BaseModel):
    total: int
    items: list[TopicResponse]


class CollectResponse(BaseModel):
    results: dict[str, int] = Field(default_factory=dict)
    message: str = "ok"
