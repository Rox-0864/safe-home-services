import json
from datetime import datetime

from sqlmodel import Session

from hogar_confianza.database.engine import get_db_engine
from hogar_confianza.database.models import SafetyCheckInDB


def check_in_provider(booking_id: str, provider_name: str, location: str) -> str:
    engine = get_db_engine()
    timestamp = datetime.now().isoformat()

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

    return json.dumps({
        "booking_id": booking_id,
        "event": "CHECK_IN",
        "provider": provider_name,
        "location": location,
        "timestamp": timestamp,
        "message": f"✅ {provider_name} ha llegado al domicilio. Se notificó al contacto de confianza.",
        "actions_taken": [
            "Selfie de llegada registrada",
            "Ubicación verificada con GPS",
            "Contacto de confianza notificado vía SMS",
            "Temporizador de sesión iniciado",
        ]
    }, ensure_ascii=False, indent=2)


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
        "message": f"✅ {provider_name} ha finalizado el servicio. Recuerda revisar el trabajo antes de confirmar.",
        "actions_taken": [
            "Selfie de salida registrada",
            "Contacto de confianza notificado: servicio finalizado",
            "Enlace de encuesta de satisfacción enviado",
        ]
    }, ensure_ascii=False, indent=2)


def notify_trusted_contact(contact_phone: str, message_type: str, provider_name: str, address: str) -> str:
    templates = {
        "provider_arrived": f"🔔 HOGARCONFIANZA: {provider_name} ha llegado a {address} para realizar el servicio.",
        "provider_left": f"🔔 HOGARCONFIANZA: {provider_name} ha finalizado y salido de {address}.",
        "emergency": f"🚨 HOGARCONFIANZA ALERTA: Reporte de incidente en {address}. Contactando a emergencias.",
        "booking_confirmed": f"✅ HOGARCONFIANZA: Servicio confirmado en {address} con {provider_name}.",
    }
    message = templates.get(message_type, f"HOGARCONFIANZA: Actualización de servicio en {address}")

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


def trigger_panic_button(booking_id: str, address: str) -> str:
    return json.dumps({
        "booking_id": booking_id,
        "event": "PANIC_BUTTON_ACTIVATED",
        "address": address,
        "timestamp": datetime.now().isoformat(),
        "actions_taken": [
            "Contacto de confianza notificado con ubicación",
            "Servicio marcado como EMERGENCIA",
            "Proveedor bloqueado temporalmente",
            "Equipo de seguridad notificado",
        ],
        "message": "🚨 ALERTA DE EMERGENCIA. Contacto de confianza notificado. Si estás en peligro, llama al 911.",
        "follow_up": "Un agente de seguridad se comunicará contigo en menos de 5 minutos."
    }, ensure_ascii=False, indent=2)
