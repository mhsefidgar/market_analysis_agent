from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class AnalysisRequest(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=200)
    competitors: List[str] = Field(default_factory=list, max_length=10)
    market_segment: Optional[str] = Field(default=None, max_length=200)

    @field_validator("product_name", "market_segment")
    @classmethod
    def strip_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        return value or None


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolExecution(BaseModel):
    tool_name: str
    status: str
    duration_ms: float
    error: Optional[str] = None


class AgentResponse(BaseModel):
    report: str
    tool_calls_made: int = 0
    execution_trace: List[ToolExecution] = Field(default_factory=list)


class AnalysisStatus(BaseModel):
    task_id: str
    status: TaskStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[AgentResponse] = None
    error: Optional[str] = None

    model_config = {"use_enum_values": True}
