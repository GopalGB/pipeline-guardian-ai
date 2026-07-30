from sqlalchemy.orm import Session
import pytest

from app.db import Incident, Pipeline, PipelineRun, create_database
from app.domain import IncidentState
from app.recovery import decide, retry_once


class Adapter:
    calls = 0
    def retry_failed_task(self, task): self.calls += 1; return True


def test_approval_retry_is_idempotent_and_rejection_refuses_retry(tmp_path):
    engine = create_database(f"sqlite:///{tmp_path / 'db.sqlite'}")
    adapter = Adapter()
    with Session(engine) as session:
        pipeline = Pipeline(source="fixture", connector_config={}); session.add(pipeline); session.flush()
        run = PipelineRun(pipeline_id=pipeline.id, run_id="run", task_id="task", state="failed", evidence={}); session.add(run); session.flush()
        incident = Incident(pipeline_run_id=run.id, state=IncidentState.AWAITING_APPROVAL.value, evidence={"task": "extract"})
        session.add(incident); session.commit()
        decide(session, incident, actor="op", approved=True, reason="reviewed")
        retry_once(session, incident, adapter); retry_once(session, incident, adapter)
        assert incident.state == IncidentState.HEALED.value and adapter.calls == 1
        rejected = Incident(pipeline_run_id=run.id, state=IncidentState.AWAITING_APPROVAL.value, evidence={})
        session.add(rejected); session.commit()
        decide(session, rejected, actor="op", approved=False, reason="unsafe")
        with pytest.raises(ValueError): retry_once(session, rejected, adapter)
