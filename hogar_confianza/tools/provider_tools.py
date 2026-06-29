import json
import random
import unicodedata
from datetime import datetime

from sqlmodel import Session, select

from hogar_confianza.database.engine import get_db_engine
from hogar_confianza.database.models import BookingDB, ProviderDB


def _normalize(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


def search_providers(service_type: str, zip_code: str) -> str:
    engine = get_db_engine()
    with Session(engine) as session:
        stmt = select(ProviderDB).where(ProviderDB.service == _normalize(service_type))
        providers = session.exec(stmt).all()

        matches = [p for p in providers if zip_code in p.zip_codes]
        if not matches:
            matches = list(providers)

        matches.sort(key=lambda p: p.trust_score, reverse=True)

        result = []
        for p in matches:
            result.append({
                "id": p.id,
                "name": p.name,
                "service": p.service,
                "rating": p.rating,
                "verified": p.verified,
                "years_experience": p.years_experience,
                "has_insurance": p.has_insurance,
                "completed_jobs": p.completed_jobs,
                "trust_score": p.trust_score,
            })
        return json.dumps(result, ensure_ascii=False, indent=2)


def get_provider_details(provider_id: str) -> str:
    engine = get_db_engine()
    with Session(engine) as session:
        provider = session.get(ProviderDB, provider_id)
        if not provider:
            return json.dumps({"error": "Proveedor no encontrado"})
        return json.dumps({
            "id": provider.id,
            "name": provider.name,
            "service": provider.service,
            "rating": provider.rating,
            "verified": provider.verified,
            "zip_codes": provider.zip_codes,
            "phone": provider.phone,
            "years_experience": provider.years_experience,
            "has_insurance": provider.has_insurance,
            "completed_jobs": provider.completed_jobs,
            "trust_score": provider.trust_score,
        }, ensure_ascii=False, indent=2)


def verify_provider_background(provider_id: str) -> str:
    engine = get_db_engine()
    with Session(engine) as session:
        provider = session.get(ProviderDB, provider_id)
        if not provider:
            return json.dumps({"error": "Proveedor no encontrado"})

        issues = []
        if not provider.verified:
            issues.append("El proveedor NO ha completado el proceso de verificación de identidad")
        if not provider.has_insurance:
            issues.append("El proveedor NO cuenta con seguro de responsabilidad civil")
        if provider.trust_score < 3.5:
            issues.append("El puntaje de confianza está por debajo del mínimo recomendado")
        if provider.completed_jobs < 50:
            issues.append("Poca experiencia: menos de 50 trabajos completados")

        verdict = "APROBADO" if not issues else "REQUIERE_REVISION"
        return json.dumps({
            "provider_id": provider_id,
            "provider_name": provider.name,
            "verification_status": verdict,
            "issues": issues if issues else ["Sin problemas encontrados"],
            "trust_score": provider.trust_score,
            "recommendation": "Se recomienda contratar" if verdict == "APROBADO" else (
                "Se recomienda entrevistar antes de contratar"
            ),
        }, ensure_ascii=False, indent=2)


def create_escrow_booking(
    provider_id: str,
    service_type: str,
    description: str,
    amount: float,
    scheduled_date: str,
    scheduled_time: str,
    user_name: str,
    user_phone: str
) -> str:
    booking_id = f"BK-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"
    booking = BookingDB(
        id=booking_id,
        user_id=user_phone,
        provider_id=provider_id,
        service=service_type.lower(),
        description=description,
        status="PENDIENTE_APROBACION",
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        amount=amount,
        escrow_held=False,
    )

    engine = get_db_engine()
    with Session(engine) as session:
        session.add(booking)
        session.commit()

    return json.dumps({
        "booking_id": booking_id,
        "status": "PENDIENTE_APROBACION",
        "message": f"Reserva {booking_id} creada. El usuario debe aprobar el depósito en garantía de ${amount:,.2f} MXN antes de confirmar.",
        "amount_held": amount,
        "release_conditions": [
            "El pago se libera al proveedor 48h después de completar el servicio",
            "El usuario puede reportar incidentes durante la ventana de 48h",
            "Si hay disputa, el monto queda retenido hasta resolución",
        ]
    }, ensure_ascii=False, indent=2)


def approve_booking(booking_id: str) -> str:
    engine = get_db_engine()
    with Session(engine) as session:
        booking = session.get(BookingDB, booking_id)
        if not booking:
            return json.dumps({"error": "Reserva no encontrada"})

        booking.status = "CONFIRMADA"
        booking.escrow_held = True
        session.add(booking)
        session.commit()

        return json.dumps({
            "booking_id": booking_id,
            "status": "CONFIRMADA",
            "message": f"Reserva {booking_id} confirmada. El pago de ${booking.amount:,.2f} MXN está retenido en garantía.",
        }, ensure_ascii=False, indent=2)


def reject_booking(booking_id: str) -> str:
    engine = get_db_engine()
    with Session(engine) as session:
        booking = session.get(BookingDB, booking_id)
        if not booking:
            return json.dumps({"error": "Reserva no encontrada"})

        booking.status = "RECHAZADA"
        session.add(booking)
        session.commit()

        return json.dumps({
            "booking_id": booking_id,
            "status": "RECHAZADA",
            "message": f"Reserva {booking_id} rechazada. No se realizó ningún cargo.",
        }, ensure_ascii=False, indent=2)


def release_payment(booking_id: str, provider_confirmed: bool, user_confirmed: bool) -> str:
    engine = get_db_engine()
    with Session(engine) as session:
        booking = session.get(BookingDB, booking_id)
        if not booking:
            return json.dumps({"error": "Reserva no encontrada"})

        if not provider_confirmed or not user_confirmed:
            return json.dumps({
                "booking_id": booking_id,
                "status": "RETENIDO",
                "message": "Ambas partes deben confirmar la finalización del servicio para liberar el pago.",
            })

        booking.status = "COMPLETADA"
        booking.escrow_held = False
        session.add(booking)
        session.commit()

        return json.dumps({
            "booking_id": booking_id,
            "status": "COMPLETADA",
            "message": f"Pago de ${booking.amount:,.2f} MXN liberado al proveedor. Los 48h de ventana de reclamos han iniciado.",
        }, ensure_ascii=False, indent=2)
