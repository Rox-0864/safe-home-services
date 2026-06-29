from google.adk import Agent

from hogar_confianza._model import resolve_model_with_fallback
from hogar_confianza.i18n import get_prompt

triage_agent = Agent(
    name="triage_agent",
    model=resolve_model_with_fallback(),
    instruction=lambda _ctx: get_prompt("triage"),
    description="Clasifica solicitudes de servicio doméstico. Transfiere a matching_agent cuando identifica el tipo de servicio.",
)
