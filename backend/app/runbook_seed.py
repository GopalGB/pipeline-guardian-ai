from sqlalchemy.orm import Session

from app.db import Runbook


RUNBOOKS = [{"title": "Failed extract task", "body": "For extract task failures, inspect upstream credentials and retry_failed_task after approval.", "tags": ["extract", "failed"]}]


def seed_runbooks(session: Session) -> None:
    if session.query(Runbook).count() == 0:
        session.add_all([Runbook(**runbook) for runbook in RUNBOOKS])
        session.commit()

