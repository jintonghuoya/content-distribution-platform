import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlatformConfigCreate(BaseModel):
    display_name: str = ""
    api_key: str = ""
    cookie: str = ""
    app_secret: str = ""
    app_id: str = ""
    extra: dict[str, Any] | None = None


class PlatformConfigResponse(BaseModel):
    id: int
    name: str
    display_name: str
    api_key: str = ""
    cookie: str = ""
    app_secret: str = ""
    app_id: str = ""
    extra: dict[str, Any] | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}
