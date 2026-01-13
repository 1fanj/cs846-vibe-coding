from sqlmodel import SQLModel, create_engine, Session
import os
from typing import Generator


_engine = None


def init_engine():
    global _engine
    DATABASE_URL = os.environ.get("VIBE_DATABASE_URL", "sqlite:///./vibe.db")
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    _engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db():
    if _engine is None:
        init_engine()
    SQLModel.metadata.create_all(_engine)


def get_session() -> Generator[Session, None, None]:
    if _engine is None:
        init_engine()
    with Session(_engine) as session:
        yield session
