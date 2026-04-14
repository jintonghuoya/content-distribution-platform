import datetime
from typing import Any

from pydantic import BaseModel, Field


class FilterResult(BaseModel):
    passed: bool
    category: str | None = None
    priority_score: float = 0.0
    reason: str = ""


class FilterRuleCreate(BaseModel):
    name: str
    rule_type: str
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    run_order: int = 0


class FilterRuleResponse(BaseModel):
    id: int
    name: str
    rule_type: str
    config: dict[str, Any]
    enabled: bool
    run_order: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class FilterTriggerResponse(BaseModel):
    total: int
    filtered: int
    rejected: int
    message: str = "ok"
