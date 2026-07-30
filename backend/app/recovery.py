from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import Incident, PipelineRun, append_audit_event
from app.domain import IncidentState, PipelineTask, TaskState, transition_incident


def decide(session: Session, incident: Incident, *, actor: str, approved: bool, reason: str) -> Incident:
    target = IncidentState.APPROVED if approved else IncidentState.REJECTED
    transition_incident(IncidentState(incident.state), target)
    incident.state = target.value
    incident.decision = {"actor": actor, "reason": reason, "created_at": datetime.now(timezone.utc).isoformat()}
    append_audit_event(session, event_type="approved" if approved else "rejected", actor=actor,
                       incident_id=incident.id, payload=incident.decision)
    session.commit()
    return incident


def retry_once(session: Session, incident: Incident, adapter) -> Incident:
    if incident.action is not None:
        return incident
    if incident.state != IncidentState.APPROVED.value:
        raise ValueError("retry requires approval")
    transition_incident(IncidentState.APPROVED, IncidentState.EXECUTING)
    incident.state = IncidentState.EXECUTING.value
    run = session.get(PipelineRun, incident.pipeline_run_id)
    if run is None:
        raise ValueError("incident run not found")
    task = PipelineTask(source=run.pipeline.source if run.pipeline else "stored", run_id=run.run_id,
                        task_id=run.task_id, state=TaskState.FAILED, evidence=incident.evidence)
    ok = adapter.retry_failed_task(task)
    incident.action = {"action_id": "retry_failed_task", "dispatched": ok}
    incident.state = IncidentState.HEALED.value if ok else IncidentState.ACTION_FAILED.value
    append_audit_event(session, event_type="dispatch", actor="system", incident_id=incident.id, payload=incident.action)
    append_audit_event(session, event_type="verification", actor="system", incident_id=incident.id,
                       payload={"state": incident.state})
    session.commit()
    return incident
