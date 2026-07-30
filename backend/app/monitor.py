import hashlib
import json
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Incident, Pipeline, PipelineRun, append_audit_event
from app.domain import IncidentState, PipelineTask, TaskState


def evidence_fingerprint(task: PipelineTask) -> str:
    safe = json.dumps({"source": task.source, "run_id": task.run_id, "task_id": task.task_id,
                       "state": task.state.value, "evidence": task.evidence}, sort_keys=True)
    return hashlib.sha256(safe.encode()).hexdigest()


def bounded_evidence(task: PipelineTask) -> dict:
    def redact(value: str) -> str:
        value = re.sub(r"(?i)(api[_-]?key|token|password)=\S+", r"\1=[REDACTED]", value)
        return value[:4000]
    return {key: redact(str(value)) if isinstance(value, str) else value for key, value in task.evidence.items()}


@dataclass
class MonitorResult:
    incidents_created: int
    tasks_seen: int


def run_monitoring_cycle(session: Session, adapter) -> MonitorResult:
    created = 0
    tasks = adapter.poll()
    for task in tasks:
        if task.state is not TaskState.FAILED:
            continue
        fingerprint = evidence_fingerprint(task)
        pipeline = session.scalar(select(Pipeline).where(Pipeline.source == task.source))
        if pipeline is None:
            pipeline = Pipeline(source=task.source, connector_config={})
            session.add(pipeline)
            session.flush()
        run = PipelineRun(pipeline_id=pipeline.id, run_id=task.run_id, task_id=task.task_id,
                          state=task.state.value, evidence_fingerprint=fingerprint, evidence=bounded_evidence(task))
        session.add(run)
        session.flush()
        duplicate = session.scalar(select(Incident).join(PipelineRun).where(PipelineRun.evidence_fingerprint == fingerprint))
        if duplicate is None:
            incident = Incident(pipeline_run_id=run.id, state=IncidentState.DETECTED.value, evidence=run.evidence)
            session.add(incident)
            session.flush()
            append_audit_event(session, event_type="detected", actor="system", incident_id=incident.id,
                               payload={"fingerprint": fingerprint})
            created += 1
    session.commit()
    return MonitorResult(incidents_created=created, tasks_seen=len(tasks))

