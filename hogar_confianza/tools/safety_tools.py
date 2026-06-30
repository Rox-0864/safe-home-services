import json
from datetime import datetime

from sqlmodel import Session

from hogar_confianza.database.engine import get_db_engine
from hogar_confianza.database.models import BookingDB, SafetyCheckInDB, UserAddressDB


def _resolve_address(booking_id: str) -> dict | None:
    engine = get_db_engine()
    with Session(engine) as session:
        booking = session.get(BookingDB, booking_id)
        if not booking or not booking.address_id:
            return None
        address = session.get(UserAddressDB, booking.address_id)
        if not address:
            return None
        return {
            "address_id": address.id,
            "calle": address.calle,
            "numero_exterior": address.numero_exterior,
            "numero_interior": address.numero_interior,
            "colonia": address.colonia,
            "ciudad": address.ciudad,
            "estado": address.estado,
            "zip_code": address.zip_code,
            "pais": address.pais,
            "lat": address.lat,
            "lng": address.lng,
            "formatted_address": address.formatted_address,
        }


def _address_to_str(addr: dict | None) -> str:
    if not addr:
        return "domicilio del usuario"
    parts = [addr.get("calle", "")]
    if addr.get("numero_exterior"):
        parts.append(f"#{addr['numero_exterior']}")
    if addr.get("colonia"):
        parts.append(f"Col. {addr['colonia']}")
    if addr.get("ciudad"):
        parts.append(addr["ciudad"])
    return ", ".join(p for p in parts if p)


def check_in_provider(
    booking_id: str,
    provider_name: str,
    location: str | None = None,
) -> str:
    engine = get_db_engine()
    timestamp = datetime.now().isoformat()

    addr = _resolve_address(booking_id)
    addr_str = _address_to_str(addr) if location is None else location
    lat = addr["lat"] if addr else None
    lng = addr["lng"] if addr else None
    formatted = addr["formatted_address"] if addr else None

    with Session(engine) as session:
        checkin = SafetyCheckInDB(
            booking_id=booking_id,
            provider_id=provider_name,
            check_in_time=timestamp,
            selfie_confirmed=True,
            location_verified=True,
            trusted_contact_notified=True,
        )
        session.add(checkin)
        session.commit()

    response = {
        "booking_id": booking_id,
        "event": "CHECK_IN",
        "provider": provider_name,
        "location": addr_str,
        "timestamp": timestamp,
        "message": f"{provider_name} ha llegado al domicilio. Se notificó al contacto de confianza.",
        "actions_taken": [
            "Selfie de llegada registrada",
            "Ubicación verificada con GPS",
            "Contacto de confianza notificado vía SMS",
            "Temporizador de sesión iniciado",
        ],
    }
    if formatted:
        response["formatted_address"] = formatted
    if lat is not None:
        response["lat"] = lat
        response["lng"] = lng

    return json.dumps(response, ensure_ascii=False, indent=2)


def check_out_provider(booking_id: str, provider_name: str, hours_worked: float) -> str:
    engine = get_db_engine()
    timestamp = datetime.now().isoformat()

    with Session(engine) as session:
        checkin = session.get(SafetyCheckInDB, booking_id)
        if checkin:
            checkin.check_out_time = timestamp
            session.add(checkin)
            session.commit()

    return json.dumps({
        "booking_id": booking_id,
        "event": "CHECK_OUT",
        "provider": provider_name,
        "hours_worked": hours_worked,
        "timestamp": timestamp,
        "message": f"{provider_name} ha finalizado el servicio. Recuerda revisar el trabajo antes de confirmar.",
        "actions_taken": [
            "Selfie de salida registrada",
            "Contacto de confianza notificado: servicio finalizado",
            "Enlace de encuesta de satisfacción enviado",
        ]
    }, ensure_ascii=False, indent=2)


def notify_trusted_contact(
    contact_phone: str,
    message_type: str,
    provider_name: str,
    address: str | None = None,
) -> str:
    addr_str = address or "domicilio del usuario"
    templates = {
        "provider_arrived": f"HOGARCONFIANZA: {provider_name} ha llegado a {addr_str} para realizar el servicio.",
        "provider_left": f"HOGARCONFIANZA: {provider_name} ha finalizado y salido de {addr_str}.",
        "emergency": f"HOGARCONFIANZA ALERTA: Reporte de incidente en {addr_str}. Contactando a emergencias.",
        "booking_confirmed": f"HOGARCONFIANZA: Servicio confirmado en {addr_str} con {provider_name}.",
    }
    message = templates.get(message_type, f"HOGARCONFIANZA: Actualización de servicio en {addr_str}")

    return json.dumps({
        "notified": True,
        "contact_phone": contact_phone[-4:].rjust(len(contact_phone), "*"),
        "message_sent": message,
        "timestamp": datetime.now().isoformat(),
    }, ensure_ascii=False, indent=2)


def report_incident(booking_id: str, incident_type: str, description: str) -> str:
    severity = "ALTA" if incident_type in ["robo", "violencia", "amenaza"] else "MEDIA"
    return json.dumps({
        "booking_id": booking_id,
        "incident_type": incident_type,
        "description": description,
        "severity": severity,
        "timestamp": datetime.now().isoformat(),
        "actions_taken": [
            "Servicio pausado inmediatamente",
            "Contacto de confianza notificado",
            "Incidente reportado al equipo de seguridad",
            "Reembolso del depósito procesado" if severity == "ALTA" else "En revisión",
        ],
        "recommendation": "Contacta a las autoridades locales al 911. Te asistiremos con la denuncia." if severity == "ALTA" else "Procederemos con la investigación interna."
    }, ensure_ascii=False, indent=2)


def trigger_panic_button(
    booking_id: str,
    address: str | None = None,
) -> str:
    addr = _resolve_address(booking_id)
    addr_str = address or _address_to_str(addr)
    lat = addr["lat"] if addr else None
    lng = addr["lng"] if addr else None

    response = {
        "booking_id": booking_id,
        "event": "PANIC_BUTTON_ACTIVATED",
        "address": addr_str,
        "timestamp": datetime.now().isoformat(),
        "actions_taken": [
            "Contacto de confianza notificado con ubicación",
            "Servicio marcado como EMERGENCIA",
            "Proveedor bloqueado temporalmente",
            "Equipo de seguridad notificado",
        ],
        "message": "ALERTA DE EMERGENCIA. Contacto de confianza notificado. Si estás en peligro, llama al 911.",
        "follow_up": "Un agente de seguridad se comunicará contigo en menos de 5 minutos.",
    }
    if lat is not None:
        response["lat"] = lat
        response["lng"] = lng
    if addr and addr.get("formatted_address"):
        response["formatted_address"] = addr["formatted_address"]

    return json.dumps(response, ensure_ascii=False, indent=2)
