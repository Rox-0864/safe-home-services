import pytest

from hogar_confianza.database.engine import get_engine, get_session, init_db, set_db_engine
from hogar_confianza.database.seed import seed_providers


@pytest.fixture(autouse=True)
def db_engine():
    engine = get_engine(test=True)
    set_db_engine(engine)
    init_db(engine)
    seed_providers(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    with get_session(db_engine) as session:
        yield session
