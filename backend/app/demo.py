import os
from pathlib import Path

from app.adapters.fixture import FixtureAdapter
from app.analysis import AnalysisResult
from app.main import create_app


fixture = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "airflow_failed_run.json"


class DeterministicDemoAnalyzer:
    """Local-only analyzer so the demo never needs a provider credential."""

    def analyze(self, evidence: dict, runbooks: list[dict]) -> AnalysisResult:
        return AnalysisResult(summary="extract task failed", confidence=0.9,
                              action_id="retry_failed_task",
                              rationale="matched the failed extract runbook")


app = create_app(os.getenv("DATABASE_URL", "sqlite:///./pipeline_guardian.db"),
                 FixtureAdapter(fixture), DeterministicDemoAnalyzer())
