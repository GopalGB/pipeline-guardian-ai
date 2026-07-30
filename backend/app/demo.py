import os
from pathlib import Path

from app.adapters.fixture import FixtureAdapter
from app.main import create_app


fixture = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "airflow_failed_run.json"
app = create_app(os.getenv("DATABASE_URL", "sqlite:///./pipeline_guardian.db"), FixtureAdapter(fixture))
