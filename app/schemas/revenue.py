import datetime
from typing import Any

from pydantic import BaseModel, Field


class RevenueRecordResponse(BaseModel):
    id: int
    distribution_id: int
    platform: str
    content_id: int
    topic_id: int | None
    views: int
    likes: int
    comments: int
    shares: int
    revenue_amount: float
    currency: str
    recorded_at: datetime.datetime
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class RevenueSummary(BaseModel):
    total_revenue: float = 0.0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    by_platform: dict[str, dict[str, Any]] = Field(default_factory=dict)
    record_count: int = 0
