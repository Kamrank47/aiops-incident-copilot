from typing import Literal

from pydantic import BaseModel, Field


class Alert(BaseModel):
    status: str = "firing"
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: str | None = None


class AlertmanagerPayload(BaseModel):
    """Subset of the Alertmanager webhook v4 payload."""

    status: str = "firing"
    alerts: list[Alert] = Field(default_factory=list)


class Context(BaseModel):
    metrics: dict[str, str] = Field(default_factory=dict)
    log_lines: list[str] = Field(default_factory=list)
    recent_deploys: list[str] = Field(default_factory=list)


class Triage(BaseModel):
    summary: str
    likely_cause: str
    confidence: Literal["low", "medium", "high"]
    next_steps: list[str]
    source: Literal["llm", "fallback"] = "llm"
