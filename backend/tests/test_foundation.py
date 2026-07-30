import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.db import append_audit_event, create_database, read_audit_events
from app.domain import IncidentState, transition_incident


def test_database_creates_only_five_approved_models(tmp_path):
    engine = create_database(f"sqlite:///{tmp_path / 'foundation.db'}")
    assert set(inspect(engine).get_table_names()) == {"pipelines", "pipeline_runs", "incidents", "runbooks", "audit_events"}


def test_incident_transition_guard():
    assert transition_incident(IncidentState.DETECTED, IncidentState.ANALYZED) == IncidentState.ANALYZED
    with pytest.raises(ValueError):
        transition_incident(IncidentState.DETECTED, IncidentState.HEALED)
    with pytest.raises(ValueError):
        transition_incident(IncidentState.ANALYSIS_FAILED, IncidentState.APPROVED)


def test_audit_is_insert_and_read_only_after_reconnect(tmp_path):
    engine = create_database(f"sqlite:///{tmp_path / 'audit.db'}")
    with Session(engine) as session:
        append_audit_event(session, event_type="detected", actor="system", payload={"safe": True})
    with Session(engine) as session:
        events = read_audit_events(session)
        assert [(event.event_type, event.payload) for event in events] == [("detected", {"safe": True})]
    assert not hasattr(type(events[0]), "update")
    assert not hasattr(type(events[0]), "delete")


def test_project_isolation():
    root = Path(__file__).parents[2]
    legacy = {"final_to_faiz", "knowledge", "downloads", "Q&A Dataset for Janvi"}
    for path in (root / "backend").rglob("*.py"):
        assert not any(part in legacy for part in path.parts)
        assert path.is_file()
    assert importlib.util.find_spec("final_to_faiz") is None
