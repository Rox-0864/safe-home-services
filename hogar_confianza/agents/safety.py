from google.adk import Agent

from hogar_confianza._model import resolve_model_with_fallback
from hogar_confianza.i18n import get_prompt
from hogar_confianza.tools.safety_tools import (
    check_in_provider,
    check_out_provider,
    notify_trusted_contact,
    report_incident,
    trigger_panic_button,
)

safety_agent = Agent(
    name="safety_agent",
    model=resolve_model_with_fallback(),
    instruction=lambda _ctx: get_prompt("safety"),
    description="Gestiona la seguridad durante el servicio: check-in/out, contacto de confianza, botón de pánico.",
    tools=[check_in_provider, check_out_provider, notify_trusted_contact, report_incident, trigger_panic_button],
)
