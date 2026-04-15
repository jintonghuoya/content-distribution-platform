import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class GenerationResult(BaseModel):
    content_type: str
    title: str
    body: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GeneratedContentResponse(BaseModel):
    id: int
    topic_id: int
    content_type: str
    title: str
    body: str
    prompt_name: str
    llm_model: str
    status: str
    metadata: dict[str, Any] | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @field_validator("metadata", mode="before")
    @classmethod
    def coerce_metadata(cls, v):
        if isinstance(v, dict):
            return v
        return None

    model_config = {"from_attributes": True}


class GeneratedContentListResponse(BaseModel):
    total: int
    items: list[GeneratedContentResponse]


class GenerateTriggerResponse(BaseModel):
    total: int
    generated: int
    message: str = "ok"
