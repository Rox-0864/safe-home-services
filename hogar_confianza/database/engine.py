import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

_override_engine = None


def set_db_engine(engine):
    global _override_engine
    _override_engine = engine


def get_db_engine():
    global _override_engine
    if _override_engine is not None:
        return _override_engine
    return get_engine()


def get_engine_url(test: bool = False) -> str:
    if test:
        return "sqlite:///:memory:"
    return os.getenv("DATABASE_URL") or f"sqlite:///{Path(__file__).parent.parent.parent / 'hogar_confianza.db'}"


def get_engine(test: bool = False):
    return create_engine(get_engine_url(test), echo=False)


def init_db(engine):
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session(engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

