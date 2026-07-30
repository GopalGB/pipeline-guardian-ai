from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Incident, PipelineRun, append_audit_event, read_audit_events
from app.domain import IncidentState, transition_incident
from app.analysis import analyze_once
from app.monitor import run_monitoring_cycle
from app.retrieval import retrieve_runbooks
from app.recovery import decide, retry_once


class DecisionRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=1000)


def create_router(session_factory, adapter, analyzer=None) -> APIRouter:
    router = APIRouter()
    def session_dep():
        with session_factory() as session:
            yield session
    @router.get("/incidents")
    def incidents(session: Session = Depends(session_dep)):
        return [_serialize(item, session) for item in session.scalars(select(Incident)).all()]
    @router.get("/incidents/{incident_id}")
    def incident(incident_id: int, session: Session = Depends(session_dep)):
        item = session.get(Incident, incident_id)
        if item is None: raise HTTPException(404, "incident not found")
        return {"id": item.id, "state": item.state, "evidence": item.evidence, "analysis": item.analysis,
                "retrieved_runbooks": item.retrieved_runbooks,
                "decision": item.decision, "action": item.action,
                "audit": _audit(session, incident_id)}
    @router.post("/poll")
    def poll(session: Session = Depends(session_dep)):
        result = run_monitoring_cycle(session, adapter)
        return {"incidents_created": result.incidents_created, "tasks_seen": result.tasks_seen}
    @router.post("/incidents/{incident_id}/analyze")
    def analyze(incident_id: int, session: Session = Depends(session_dep)):
        if analyzer is None:
            raise HTTPException(503, "analysis provider is not configured")
        item = session.get(Incident, incident_id)
        if item is None:
            raise HTTPException(404, "incident not found")
        run = session.get(PipelineRun, item.pipeline_run_id)
        query = " ".join([run.task_id if run else "", *[str(value) for value in item.evidence.values()]])
        books = retrieve_runbooks(session, query)
        result = analyze_once(item, analyzer, [book.body for book in books], session)
        if result is None:
            session.commit()
            raise HTTPException(422, "analysis failed")
        transition_incident(IncidentState.ANALYZED, IncidentState.AWAITING_APPROVAL)
        item.state = IncidentState.AWAITING_APPROVAL.value
        append_audit_event(session, event_type="awaiting_approval", actor="system", incident_id=item.id)
        session.commit()
        return _serialize(item, session)
    @router.post("/incidents/{incident_id}/approve")
    def approve(incident_id: int, request: DecisionRequest, session: Session = Depends(session_dep)):
        item = session.get(Incident, incident_id)
        if item is None: raise HTTPException(404, "incident not found")
        try: return decide(session, item, actor=request.actor, approved=True, reason=request.reason)
        except ValueError as exc: raise HTTPException(409, str(exc)) from exc
    @router.post("/incidents/{incident_id}/reject")
    def reject(incident_id: int, request: DecisionRequest, session: Session = Depends(session_dep)):
        item = session.get(Incident, incident_id)
        if item is None: raise HTTPException(404, "incident not found")
        try: return decide(session, item, actor=request.actor, approved=False, reason=request.reason)
        except ValueError as exc: raise HTTPException(409, str(exc)) from exc
    @router.post("/incidents/{incident_id}/retry")
    def retry(incident_id: int, session: Session = Depends(session_dep)):
        item = session.get(Incident, incident_id)
        if item is None: raise HTTPException(404, "incident not found")
        try: return retry_once(session, item, adapter)
        except ValueError as exc: raise HTTPException(409, str(exc)) from exc
    return router


def _serialize(item: Incident, session: Session) -> dict:
    return {"id": item.id, "state": item.state, "evidence": item.evidence,
            "retrieved_runbooks": item.retrieved_runbooks, "analysis": item.analysis,
            "decision": item.decision, "action": item.action, "audit": _audit(session, item.id)}


def _audit(session: Session, incident_id: int) -> list[dict]:
    return [{"event_type": event.event_type, "actor": event.actor, "payload": event.payload}
            for event in read_audit_events(session, incident_id)]
