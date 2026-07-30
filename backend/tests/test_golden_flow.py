import json

from sqlalchemy.orm import Session

from app.adapters.fixture import FixtureAdapter
from app.analysis import AnalysisResult, analyze_once
from app.db import Incident, create_database, read_audit_events
from app.domain import IncidentState
from app.monitor import run_monitoring_cycle
from app.recovery import decide, retry_once
from app.retrieval import retrieve_runbooks
from app.runbook_seed import seed_runbooks


class TestOnlyAnalyzer:
    """Deterministic test double; never constructed by normal runtime code."""
    def analyze(self, evidence, runbooks):
        return AnalysisResult(summary="extract failure", confidence=1, action_id="retry_failed_task", rationale="fixture runbook")


def test_deterministic_golden_flow(tmp_path):
    fixture = tmp_path / "failed.json"
    fixture.write_text(json.dumps({"source": "fixture", "run_id": "run-1", "task_id": "extract", "state": "failed", "evidence": {"log": "extract failed"}}))
    engine = create_database(f"sqlite:///{tmp_path / 'db.sqlite'}")
    adapter = FixtureAdapter(fixture)
    with Session(engine) as session:
        seed_runbooks(session)
        assert run_monitoring_cycle(session, adapter).incidents_created == 1
        incident = session.query(Incident).one()
        runbooks = retrieve_runbooks(session, "extract failed")
        assert runbooks
        assert analyze_once(incident, TestOnlyAnalyzer(), [book.body for book in runbooks])
        incident.state = IncidentState.AWAITING_APPROVAL.value
        session.commit()
        decide(session, incident, actor="test-operator", approved=True, reason="golden proof")
        retry_once(session, incident, adapter)
        assert incident.state == IncidentState.HEALED.value
        assert adapter.retry_calls == 1
        assert [event.event_type for event in read_audit_events(session, incident.id)] == ["detected", "approved", "dispatch", "verification"]

