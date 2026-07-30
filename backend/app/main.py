from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from app.api import create_router
from app.db import create_database
from app.runbook_seed import seed_runbooks


def create_app(database_url: str, adapter, analyzer=None) -> FastAPI:
    engine = create_database(database_url)
    session_factory = sessionmaker(engine)
    with session_factory() as session:
        seed_runbooks(session)
    return_app = FastAPI(title="Pipeline Guardian AI")
    return_app.include_router(create_router(session_factory, adapter, analyzer), prefix="/api")
    return return_app
