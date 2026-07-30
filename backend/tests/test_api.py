from sqlalchemy.orm import Session

from app.db import Incident, Pipeline, PipelineRun, create_database
from app.domain import IncidentState
from app.main import create_app
from app.api import create_router, DecisionRequest
from app.recovery import decide, retry_once


class Adapter:
    calls = 0
    def retry_failed_task(self, task): self.calls += 1; return True


def test_api_approval_retry_and_audit(tmp_path):
    db = create_database(f"sqlite:///{tmp_path / 'db.sqlite'}")
    with Session(db) as session:
        pipeline = Pipeline(source="fixture", connector_config={}); session.add(pipeline); session.flush()
        run = PipelineRun(pipeline_id=pipeline.id, run_id="run", task_id="task", state="failed", evidence={}); session.add(run); session.flush()
        incident = Incident(pipeline_run_id=run.id, state=IncidentState.AWAITING_APPROVAL.value, evidence={"task": "extract"})
        session.add(incident); session.commit(); incident_id = incident.id
    app = create_app(f"sqlite:///{tmp_path / 'db.sqlite'}", Adapter())
    assert "/api/incidents" in app.openapi()["paths"]
    with Session(db) as session:
        item = session.get(Incident, incident_id)
        decide(session, item, actor="op", approved=True, reason="reviewed")
        retry_once(session, item, Adapter())
        assert item.state == "healed"
