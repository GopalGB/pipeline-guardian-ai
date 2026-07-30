import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.adapters.airflow import AirflowAdapter, normalize_airflow_response
from app.adapters.fixture import FixtureAdapter
from app.db import Incident, create_database
from app.domain import TaskState
from app.monitor import run_monitoring_cycle


def test_fixture_detection_is_deduplicated_and_recovery_is_healthy(tmp_path):
    fixture = tmp_path / "failed.json"
    fixture.write_text(json.dumps({"source": "fixture", "run_id": "run-1", "task_id": "extract", "state": "failed", "evidence": {"log": "token=secret failed"}}))
    adapter = FixtureAdapter(fixture)
    engine = create_database(f"sqlite:///{tmp_path / 'db.sqlite'}")
    with Session(engine) as session:
        assert run_monitoring_cycle(session, adapter).incidents_created == 1
        for _ in range(5):
            assert run_monitoring_cycle(session, adapter).incidents_created == 0
        assert session.query(Incident).count() == 1
        assert "REDACTED" in session.query(Incident).one().evidence["log"]
        assert adapter.poll()[0].state is TaskState.FAILED


def test_airflow_normalization_is_read_only_and_contract_compatible():
    payload = {"dag_id": "orders", "run_id": "run-1", "tasks": [{"task_id": "extract", "state": "failed", "log": "x"}]}
    tasks = normalize_airflow_response(payload)
    assert tasks[0].source == "airflow"
    adapter = AirflowAdapter(payload)
    assert adapter.poll()[0].state is TaskState.FAILED
    assert adapter.mutation_calls == 0


def test_fixture_adapter_accepts_recorded_airflow_shape():
    fixture = Path(__file__).parent / "fixtures" / "airflow_failed_run.json"
    task = FixtureAdapter(fixture).poll()[0]
    assert task.source == "fixture"
    assert task.run_id == "run-1"
    assert task.state is TaskState.FAILED
