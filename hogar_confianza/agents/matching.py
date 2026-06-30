from google.adk import Agent

from hogar_confianza._model import resolve_model_with_fallback
from hogar_confianza.i18n import get_prompt
from hogar_confianza.tools import maps_tools
from hogar_confianza.tools.provider_tools import (
    get_provider_details,
    get_provider_location,
    search_providers,
    verify_provider_background,
)

matching_agent = Agent(
    name="matching_agent",
    model=resolve_model_with_fallback(),
    instruction=lambda _ctx: get_prompt("matching"),
    description="Busca y recomienda proveedores de servicio según tipo, ubicación y confiabilidad.",
    tools=[
        search_providers,
        get_provider_details,
        get_provider_location,
        verify_provider_background,
        maps_tools.geocode_address,
        maps_tools.validate_address,
        maps_tools.calculate_distance,
    ],
)
