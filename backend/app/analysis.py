from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.domain import IncidentState
from app.db import append_audit_event


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0, le=1)
    action_id: str = Field(pattern=r"^retry_failed_task$")
    rationale: str = Field(min_length=1, max_length=2000)


class Analyzer(Protocol):
    def analyze(self, evidence: dict, runbooks: list[dict]) -> AnalysisResult: ...


class ClaudeAnalyzer:
    def __init__(self, api_key: str | None, model: str | None, client=None):
        self.api_key, self.model, self.client = api_key, model, client

    def analyze(self, evidence: dict, runbooks: list[dict]) -> AnalysisResult:
        if not self.api_key or not self.model or self.client is None:
            raise RuntimeError("analysis_failed: Claude credentials, model, and client are required")
        response = self.client.create(evidence=evidence, runbooks=runbooks, model=self.model)
        return AnalysisResult.model_validate(response)


def analyze_once(incident, analyzer: Analyzer, runbooks: list[dict], session=None) -> AnalysisResult:
    if session is not None:
        incident.retrieved_runbooks = [{"body": str(item)} for item in runbooks]
        append_audit_event(session, event_type="retrieval", actor="system", incident_id=incident.id,
                           payload={"count": len(runbooks)})
    try:
        result = analyzer.analyze(incident.evidence, runbooks)
    except (RuntimeError, ValidationError, TypeError, ValueError) as exc:
        incident.state = IncidentState.ANALYSIS_FAILED.value
        incident.analysis = {"error": str(exc)[:300]}
        if session is not None:
            append_audit_event(session, event_type="analysis", actor="system", incident_id=incident.id,
                               payload={"state": incident.state})
        return None
    incident.analysis = result.model_dump()
    incident.state = IncidentState.ANALYZED.value
    if session is not None:
        append_audit_event(session, event_type="analysis", actor="system", incident_id=incident.id,
                           payload={"state": incident.state, "confidence": result.confidence})
    return result
