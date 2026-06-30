import json

from sqlmodel import Session

from hogar_confianza.database.engine import get_db_engine
from hogar_confianza.database.models import BookingDB
from hogar_confianza.tools.provider_tools import (
    approve_booking,
    create_escrow_booking,
    get_provider_details,
    reject_booking,
    release_payment,
    search_providers,
    verify_provider_background,
)
from hogar_confianza.tools.safety_tools import check_in_provider, check_out_provider


def test_search_providers_by_service_and_zip():
    result = json.loads(search_providers("plomeria", "06600"))
    assert len(result) > 0
    assert all(p["service"] == "plomeria" for p in result)
    assert result[0]["trust_score"] >= result[-1]["trust_score"]


def test_search_providers_normalizes_accents():
    result = json.loads(search_providers("plomería", "06600"))
    assert len(result) > 0
    assert result[0]["id"] == "PROV-001"


def test_search_providers_fallback_no_zip():
    result = json.loads(search_providers("plomeria", "99999"))
    assert len(result) > 0
    assert all(p["service"] == "plomeria" for p in result)


def test_search_providers_unknown_service():
    result = json.loads(search_providers("astronomia", "06600"))
    assert len(result) == 0


def test_get_provider_details():
    result = json.loads(get_provider_details("PROV-001"))
    assert result["name"] == "Juan Pérez"
    assert result["trust_score"] == 4.7


def test_get_provider_details_not_found():
    result = json.loads(get_provider_details("PROV-999"))
    assert "error" in result


def test_verify_provider_background_approved():
    result = json.loads(verify_provider_background("PROV-001"))
    assert result["verification_status"] == "APROBADO"


def test_verify_provider_background_revision():
    result = json.loads(verify_provider_background("PROV-007"))
    assert result["verification_status"] == "REQUIERE_REVISION"
    assert len(result["issues"]) > 0


def test_verify_provider_background_not_found():
    result = json.loads(verify_provider_background("PROV-999"))
    assert "error" in result


def test_create_escrow_booking():
    result = json.loads(create_escrow_booking(
        "PROV-001", "plomeria", "Fuga de agua", 1500,
        "2026-06-25", "10:00", "Test User", "+525511111111"
    ))
    assert result["status"] == "PENDIENTE_APROBACION"
    assert result["amount_held"] == 1500

    booking_id = result["booking_id"]
    engine = get_db_engine()
    with Session(engine) as session:
        booking = session.get(BookingDB, booking_id)
        assert booking is not None
        assert booking.status == "PENDIENTE_APROBACION"


def test_approve_booking():
    create = json.loads(create_escrow_booking(
        "PROV-001", "plomeria", "Fuga", 1500,
        "2026-06-25", "10:00", "Test", "+525511111111"
    ))
    booking_id = create["booking_id"]

    result = json.loads(approve_booking(booking_id))
    assert result["status"] == "CONFIRMADA"


def test_reject_booking():
    create = json.loads(create_escrow_booking(
        "PROV-001", "plomeria", "Fuga", 1500,
        "2026-06-25", "10:00", "Test", "+525511111111"
    ))
    booking_id = create["booking_id"]

    result = json.loads(reject_booking(booking_id))
    assert result["status"] == "RECHAZADA"


def test_approve_booking_not_found():
    result = json.loads(approve_booking("BK-999"))
    assert "error" in result


def test_release_payment_dual_confirmation():
    create = json.loads(create_escrow_booking(
        "PROV-001", "plomeria", "Fuga", 1500,
        "2026-06-25", "10:00", "Test", "+525511111111"
    ))
    booking_id = create["booking_id"]
    approve_booking(booking_id)

    result = json.loads(release_payment(booking_id, True, True))
    assert result["status"] == "COMPLETADA"


def test_release_payment_blocked_without_dual():
    create = json.loads(create_escrow_booking(
        "PROV-001", "plomeria", "Fuga", 1500,
        "2026-06-25", "10:00", "Test", "+525511111111"
    ))
    booking_id = create["booking_id"]
    approve_booking(booking_id)

    result = json.loads(release_payment(booking_id, False, True))
    assert result["status"] == "RETENIDO"


def test_release_payment_not_found():
    result = json.loads(release_payment("BK-999", True, True))
    assert "error" in result


def test_check_in_provider():
    result = json.loads(check_in_provider("BK-CI-001", "Juan Pérez", "Calle 123"))
    assert result["event"] == "CHECK_IN"
    assert result["provider"] == "Juan Pérez"


def test_check_out_provider():
    check_in_provider("BK-CO-001", "María García", "Av. Siempre Viva 742")
    result = json.loads(check_out_provider("BK-CO-001", "María García", 2.5))
    assert result["event"] == "CHECK_OUT"
    assert result["hours_worked"] == 2.5


def test_check_out_updates_db():
    from sqlmodel import Session

    from hogar_confianza.database.engine import get_db_engine
    from hogar_confianza.database.models import SafetyCheckInDB

    check_in_provider("BK-DBCO-001", "Carlos López", "Calle Falsa 123")
    check_out_provider("BK-DBCO-001", "Carlos López", 3.0)

    engine = get_db_engine()
    with Session(engine) as session:
        record = session.get(SafetyCheckInDB, "BK-DBCO-001")
        assert record is not None
        assert record.check_out_time is not None
