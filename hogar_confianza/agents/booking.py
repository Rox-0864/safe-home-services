from google.adk import Agent

from hogar_confianza._model import resolve_model_with_fallback
from hogar_confianza.i18n import get_prompt
from hogar_confianza.tools.provider_tools import (
    approve_booking,
    create_escrow_booking,
    reject_booking,
    release_payment,
)

booking_agent = Agent(
    name="booking_agent",
    model=resolve_model_with_fallback(),
    instruction=lambda _ctx: get_prompt("booking"),
    description="Gestiona reservas, pagos en garantía (escrow) y liberación. Requiere aprobación humana.",
    tools=[create_escrow_booking, approve_booking, reject_booking, release_payment],
)
