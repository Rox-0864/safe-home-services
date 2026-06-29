
from sqlmodel import Session, text

from hogar_confianza.database.engine import get_engine, get_engine_url, get_session, init_db
from hogar_confianza.database.models import BookingDB, ProviderDB, SafetyCheckInDB


def test_get_engine_test_mode_uses_memory():
    engine = get_engine(test=True)
    assert "memory" in str(engine.url)


def test_get_engine_prod_mode_uses_file():
    engine = get_engine(test=False)
    assert "hogar_confianza.db" in str(engine.url)


def test_get_engine_url_memory_when_test():
    assert get_engine_url(test=True) == "sqlite:///:memory:"


def test_get_engine_url_default_sqlite():
    url = get_engine_url(test=False)
    assert url.startswith("sqlite:///")
    assert "hogar_confianza.db" in url


def test_get_engine_url_uses_env_var(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    assert get_engine_url(test=False) == "postgresql://user:pass@localhost:5432/db"
    assert get_engine_url(test=True) == "sqlite:///:memory:"


def test_init_db_creates_tables():
    engine = get_engine(test=True)
    init_db(engine)
    with Session(engine) as session:
        result = session.exec(text(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )).all()
        table_names = [row[0] for row in result]
        assert "providers" in table_names
        assert "bookings" in table_names
        assert "safety_checkins" in table_names


def test_get_session_yields_active_session():
    engine = get_engine(test=True)
    init_db(engine)

    with get_session(engine) as session:
        result = session.exec(text("SELECT 1")).first()
        assert result == (1,)


def test_get_session_supports_write_then_read():
    engine = get_engine(test=True)
    init_db(engine)

    with get_session(engine) as session:
        session.exec(text("CREATE TABLE IF NOT EXISTS test_triang (id INTEGER)"))
        session.exec(text("INSERT INTO test_triang VALUES (42)"))
        session.commit()

    with get_session(engine) as session:
        result = session.exec(text("SELECT id FROM test_triang")).first()
        assert result[0] == 42


def test_provider_db_creation():
    provider = ProviderDB(
        id="PROV-001",
        name="Juan Pérez",
        service="plomeria",
        rating=4.5,
        verified=True,
        zip_codes=["06600", "06700"],
        phone="+525512345678",
        years_experience=8,
        has_insurance=True,
        completed_jobs=342,
        trust_score=4.7,
    )
    assert provider.id == "PROV-001"
    assert provider.service == "plomeria"
    assert provider.trust_score == 4.7


def test_booking_db_creation():
    booking = BookingDB(
        id="BK-20260624-001",
        user_id="user-001",
        provider_id="PROV-001",
        service="plomeria",
        description="Fuga de agua en cocina",
        status="PENDIENTE_APROBACION",
        scheduled_date="2026-06-25",
        scheduled_time="10:00",
        amount=1500.0,
        escrow_held=False,
    )
    assert booking.status == "PENDIENTE_APROBACION"
    assert booking.amount == 1500.0
    assert not booking.escrow_held


def test_provider_db_persisted():
    engine = get_engine(test=True)
    init_db(engine)

    with get_session(engine) as session:
        provider = ProviderDB(
            id="PROV-001",
            name="Juan Pérez",
            service="plomeria",
            rating=4.5,
            verified=True,
            zip_codes=["06600"],
            phone="+525512345678",
            years_experience=8,
            has_insurance=True,
            completed_jobs=342,
            trust_score=4.7,
        )
        session.add(provider)
        session.commit()

    with get_session(engine) as session:
        saved = session.get(ProviderDB, "PROV-001")
        assert saved is not None
        assert saved.name == "Juan Pérez"
        assert saved.trust_score == 4.7


def test_booking_db_persisted():
    engine = get_engine(test=True)
    init_db(engine)

    with get_session(engine) as session:
        booking = BookingDB(
            id="BK-001",
            user_id="user-001",
            provider_id="PROV-001",
            service="plomeria",
            description="Fuga",
            status="PENDIENTE_APROBACION",
            scheduled_date="2026-06-25",
            scheduled_time="10:00",
            amount=1500.0,
            escrow_held=False,
        )
        session.add(booking)
        session.commit()

    with get_session(engine) as session:
        saved = session.get(BookingDB, "BK-001")
        assert saved is not None
        assert saved.amount == 1500.0
        assert saved.status == "PENDIENTE_APROBACION"


def test_booking_status_transition():
    engine = get_engine(test=True)
    init_db(engine)

    with get_session(engine) as session:
        booking = BookingDB(
            id="BK-002",
            user_id="user-001",
            provider_id="PROV-001",
            service="plomeria",
            description="Fuga",
            status="PENDIENTE_APROBACION",
            scheduled_date="2026-06-25",
            scheduled_time="10:00",
            amount=1500.0,
            escrow_held=False,
        )
        session.add(booking)
        session.commit()

    with get_session(engine) as session:
        saved = session.get(BookingDB, "BK-002")
        saved.status = "CONFIRMADA"
        saved.escrow_held = True
        session.add(saved)
        session.commit()

    with get_session(engine) as session:
        updated = session.get(BookingDB, "BK-002")
        assert updated.status == "CONFIRMADA"
        assert updated.escrow_held


def test_seed_creates_8_providers():
    from hogar_confianza.database.seed import seed_providers

    engine = get_engine(test=True)
    init_db(engine)

    seed_providers(engine)

    with get_session(engine) as session:
        providers = session.exec(
            text("SELECT COUNT(*) FROM providers")
        ).first()
        assert providers[0] == 8


def test_seed_is_idempotent():
    from hogar_confianza.database.seed import seed_providers

    engine = get_engine(test=True)
    init_db(engine)

    seed_providers(engine)
    seed_providers(engine)

    with get_session(engine) as session:
        providers = session.exec(
            text("SELECT COUNT(*) FROM providers")
        ).first()
        assert providers[0] == 8


def test_seed_provider_has_correct_data():
    from hogar_confianza.database.seed import seed_providers

    engine = get_engine(test=True)
    init_db(engine)

    seed_providers(engine)

    with get_session(engine) as session:
        provider = session.get(ProviderDB, "PROV-001")
        assert provider is not None
        assert provider.name == "Juan Pérez"
        assert provider.service == "plomeria"
        assert provider.trust_score == 4.7


def test_safety_check_in_persisted():
    engine = get_engine(test=True)
    init_db(engine)

    with get_session(engine) as session:
        checkin = SafetyCheckInDB(
            booking_id="BK-001",
            provider_id="PROV-001",
            check_in_time="2026-06-25T10:00:00",
            selfie_confirmed=True,
            location_verified=True,
            trusted_contact_notified=True,
        )
        session.add(checkin)
        session.commit()

    with get_session(engine) as session:
        saved = session.get(SafetyCheckInDB, "BK-001")
        assert saved is not None
        assert saved.check_in_time == "2026-06-25T10:00:00"
        assert saved.selfie_confirmed
        assert saved.check_out_time is None
