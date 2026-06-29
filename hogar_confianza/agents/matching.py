from google.adk import Agent

from hogar_confianza._model import resolve_model_with_fallback
from hogar_confianza.i18n import get_prompt
from hogar_confianza.tools.provider_tools import (
    get_provider_details,
    search_providers,
    verify_provider_background,
)

matching_agent = Agent(
    name="matching_agent",
    model=resolve_model_with_fallback(),
    instruction=lambda _ctx: get_prompt("matching"),
    description="Busca y recomienda proveedores de servicio según tipo, ubicación y confiabilidad.",
    tools=[search_providers, get_provider_details, verify_provider_background],
)
