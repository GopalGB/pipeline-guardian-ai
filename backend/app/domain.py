from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskState(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
    UNKNOWN = "unknown"


class PipelineTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str = Field(min_length=1, max_length=100)
    run_id: str = Field(min_length=1, max_length=200)
    task_id: str = Field(min_length=1, max_length=200)
    state: TaskState
    failure_fingerprint: str | None = Field(default=None, max_length=128)
    evidence: dict[str, Any] = Field(default_factory=dict)


class IncidentState(StrEnum):
    DETECTED = "detected"
    ANALYZED = "analyzed"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    HEALED = "healed"
    ACTION_FAILED = "action_failed"
    ANALYSIS_FAILED = "analysis_failed"


ALLOWED_TRANSITIONS: dict[IncidentState, frozenset[IncidentState]] = {
    IncidentState.DETECTED: frozenset({IncidentState.ANALYZED, IncidentState.ANALYSIS_FAILED}),
    IncidentState.ANALYZED: frozenset({IncidentState.AWAITING_APPROVAL}),
    IncidentState.AWAITING_APPROVAL: frozenset({IncidentState.APPROVED, IncidentState.REJECTED}),
    IncidentState.APPROVED: frozenset({IncidentState.EXECUTING}),
    IncidentState.EXECUTING: frozenset({IncidentState.HEALED, IncidentState.ACTION_FAILED}),
}


def transition_incident(current: IncidentState, target: IncidentState) -> IncidentState:
    if target not in ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise ValueError(f"forbidden incident transition: {current} -> {target}")
    return target
