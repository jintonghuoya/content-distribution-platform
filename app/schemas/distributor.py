import datetime

from pydantic import BaseModel


class DistributionRecordResponse(BaseModel):
    id: int
    content_id: int
    platform: str
    success: bool
    mode: str = "published"
    platform_content_id: str
    platform_url: str
    package_data: dict | None = None
    error_message: str
    published_at: datetime.datetime
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class DistributeTriggerResponse(BaseModel):
    total: int
    distributed: int
    failed: int
    message: str = "ok"
