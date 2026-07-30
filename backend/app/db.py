from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Pipeline(Base):
    __tablename__ = "pipelines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(100), unique=True)
    connector_config: Mapped[dict] = mapped_column(JSON, default=dict)
    runs: Mapped[list["PipelineRun"]] = relationship(back_populates="pipeline")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("pipelines.id"))
    run_id: Mapped[str] = mapped_column(String(200))
    task_id: Mapped[str] = mapped_column(String(200))
    state: Mapped[str] = mapped_column(String(30))
    evidence_fingerprint: Mapped[str | None] = mapped_column(String(128))
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    pipeline: Mapped[Pipeline] = relationship(back_populates="runs")


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_run_id: Mapped[int] = mapped_column(ForeignKey("pipeline_runs.id"))
    state: Mapped[str] = mapped_column(String(30))
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    retrieved_runbooks: Mapped[list] = mapped_column(JSON, default=list)
    analysis: Mapped[dict | None] = mapped_column(JSON)
    decision: Mapped[dict | None] = mapped_column(JSON)
    action: Mapped[dict | None] = mapped_column(JSON)
    verification: Mapped[dict | None] = mapped_column(JSON)


class Runbook(Base):
    __tablename__ = "runbooks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, default=list)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int | None] = mapped_column(ForeignKey("incidents.id"))
    event_type: Mapped[str] = mapped_column(String(50))
    actor: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def create_database(database_url: str):
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    return engine


def append_audit_event(session: Session, *, event_type: str, actor: str, incident_id: int | None = None, payload: dict | None = None) -> AuditEvent:
    event = AuditEvent(event_type=event_type, actor=actor, incident_id=incident_id, payload=payload or {})
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def read_audit_events(session: Session, incident_id: int | None = None) -> list[AuditEvent]:
    statement = select(AuditEvent).order_by(AuditEvent.id)
    if incident_id is not None:
        statement = statement.where(AuditEvent.incident_id == incident_id)
    return list(session.scalars(statement))
