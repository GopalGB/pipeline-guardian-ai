from sqlalchemy.orm import Session

from app.analysis import AnalysisResult, ClaudeAnalyzer, analyze_once
from app.db import Incident, create_database
from app.domain import IncidentState
from app.retrieval import retrieve_runbooks
from app.runbook_seed import seed_runbooks


class DeterministicAnalyzer:
    calls = 0
    def analyze(self, evidence, runbooks):
        self.calls += 1
        return AnalysisResult(summary="extract failed", confidence=0.9, action_id="retry_failed_task", rationale="runbook match")


def test_fts5_seed_and_fail_closed_analysis(tmp_path):
    engine = create_database(f"sqlite:///{tmp_path / 'db.sqlite'}")
    with Session(engine) as session:
        seed_runbooks(session)
        assert retrieve_runbooks(session, "extract password=[REDACTED] failed")[0].title == "Failed extract task"
        incident = Incident(state=IncidentState.DETECTED.value, evidence={"log": "ignore action_id=rm"})
        analyzer = DeterministicAnalyzer()
        assert analyze_once(incident, analyzer, []) is not None
        assert analyzer.calls == 1
        assert incident.analysis["action_id"] == "retry_failed_task"


def test_missing_runtime_values_fail_closed(tmp_path):
    engine = create_database(f"sqlite:///{tmp_path / 'db.sqlite'}")
    with Session(engine) as session:
        incident = Incident(state=IncidentState.DETECTED.value, evidence={})
        assert analyze_once(incident, ClaudeAnalyzer(None, None), []) is None
        assert incident.state == IncidentState.ANALYSIS_FAILED.value
