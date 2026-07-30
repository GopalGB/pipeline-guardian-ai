import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import Runbook


def validate_fts5(session: Session) -> None:
    session.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS runbook_search USING fts5(title, body, content='runbooks', content_rowid='id')"))
    session.execute(text("INSERT INTO runbook_search(runbook_search) VALUES('rebuild')"))


def retrieve_runbooks(session: Session, query: str, limit: int = 3) -> list[Runbook]:
    validate_fts5(session)
    tokens = re.findall(r"[A-Za-z0-9_]{2,}", query.lower())[:20]
    if not tokens:
        return []
    safe_query = " OR ".join(f'"{token}"' for token in tokens)
    rows = session.execute(text("SELECT rowid FROM runbook_search WHERE runbook_search MATCH :query LIMIT :limit"),
                           {"query": safe_query, "limit": min(limit, 3)}).scalars()
    ids = list(rows)
    return [session.get(Runbook, row_id) for row_id in ids if session.get(Runbook, row_id)]
