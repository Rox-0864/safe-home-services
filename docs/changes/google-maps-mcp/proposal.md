# Proposal: Google Maps MCP Integration for Addresses

## Intent

Reemplazar el manejo de direcciones como strings planos por un sistema estructurado con geocoding vía Google Maps MCP. Los usuarios y proveedores tendrán direcciones geocodificadas, y los agents usarán coordenadas reales para matching por cercanía, check-in/out y notificaciones.

## Scope

### In Scope
- MCP server de Google Maps con herramientas de geocoding, validación y distancia
- Modelo `UserAddressDB` con dirección estructurada + coordenadas
- Coordenadas y radio de cobertura en `ProviderDB` (`lat`, `lng`, `service_area_km`)
- Tools Python para ADK agents (`maps_tools.py`)
- Actualización de `BookingDB` para incluir dirección del servicio
- Actualización de `safety_tools.py` para usar direcciones estructuradas
- Actualización de `search_providers` para filtrar/ordenar por distancia
- Actualización de flujo en `matching_agent` (ordenar providers por cercanía + trust_score)
- Esquemas Pydantic para Address
- Manejo graceful de API key faltante/bloqueada (modo mock)

### Out of Scope
- Autenticación de usuarios/UserDB (sigue en session_state de Streamlit)
- UI de Google Maps embed (mapa visual) — solo datos
- Pasarela de pago real
- Rate limiting en endpoints de geocoding

## Capabilities

### New Capabilities
- `address-geocoding`: Geocoding y validación de direcciones vía Google Maps API

### Modified Capabilities
- `database-persistence`: Nueva tabla UserAddress + address fields en Booking + coordenadas en Provider
- `provider-matching`: Búsqueda por cercanía geográfica además de código postal
- `safety-checkin`: Check-in/out con coordenadas reales y dirección estructurada

## Approach

1. Agregar `hogar_confianza/mcp_server/maps_server.py` — MCP server con tools:
   - `geocode_address` → address string → {lat, lng, formatted_address, components}
   - `validate_address` → address string → {valid, suggestions, geocoding}
   - `calculate_distance` → origin, destination → {km, duration}
   - `search_places` → query, restrict_to_mx → [{place_id, description}]

2. Agregar `hogar_confianza/tools/maps_tools.py` — Python functions para ADK agents
   - Misma API que el MCP server, pero como funciones invocables directamente
   - Llaman al mismo backend de Google Maps API

3. Extender `hogar_confianza/database/models.py`:
   - `UserAddressDB` — dirección estructurada con lat/lng
   - `BookingDB.address_id` — FK opcional a UserAddress

4. Actualizar schemas en `models/schemas.py`:
   - `Address` Pydantic model
   - `ServiceRequest` + address fields
   - `Booking` + address fields

5. Actualizar `database/models.py`:
   - `ProviderDB` + `lat`, `lng`, `service_area_km`, `address_formatted`

6. Actualizar `database/seed.py`:
   - Asignar coordenadas reales a los 8 providers (colonias distintas de CDMX)

7. Actualizar `tools/provider_tools.py`:
   - `create_escrow_booking` acepta address_id o dirección embebida
   - `search_providers` acepta `user_lat`, `user_lng` opcionales, ordena por distancia
   - Nueva `get_provider_location(provider_id)` tool

8. Actualizar `tools/safety_tools.py`:
   - `check_in_provider` usa lat/lng real vs. string location
   - `notify_trusted_contact` y `trigger_panic_button` usan dirección estructurada

9. Config: `GOOGLE_API_KEY` en entorno, fallback mock cuando no hay key

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `hogar_confianza/mcp_server/maps_server.py` | New | MCP server con tools de Google Maps |
| `hogar_confianza/tools/maps_tools.py` | New | Python tools para ADK agents |
| `hogar_confianza/database/models.py` | Modified | +UserAddressDB, +BookingDB.address fields, +ProviderDB.lat/lng |
| `hogar_confianza/database/seed.py` | Modified | +coordenadas en seed de 8 providers |
| `hogar_confianza/models/schemas.py` | Modified | +Address, +ServiceRequest.address, +Booking.address, +Provider.lat/lng |
| `hogar_confianza/tools/provider_tools.py` | Modified | search_providers con distancia, create_escrow_booking con dirección |
| `hogar_confianza/tools/safety_tools.py` | Modified | check-in/out con coordenadas |
| `hogar_confianza/agents/matching.py` | Modified | +maps_tools, ordenar por cercanía |
| `hogar_confianza/agents/safety.py` | Modified | +maps_tools, verificar ubicación |
| `hogar_confianza/i18n.py` | Modified | +address prompts |
| `pyproject.toml` | Modified | +requests (para Google Maps API) |
| `.env.example` | Modified | +GOOGLE_API_KEY |
| `tests/` | Modified | +tests para maps_tools |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| GOOGLE_API_KEY bloqueada | Alta | Modo mock: datos simulados con mensaje claro |
| Google Maps API cambia | Baja | Abstracción en maps_client.py, solo un punto de cambio |
| Latencia de geocoding en chat | Media | Cache en memoria de geocoding results |

## Rollback Plan

Revertir cambios en herramientas y modelos. La API pública de tools existentes NO cambia (solo se agregan parámetros opcionales).

## Dependencies

- Google Maps API key (Geocoding API + Places API)
- `requests` (o `google-maps-services-python`)

## Success Criteria

- [ ] `geocode_address("Calle 123, Colonia Centro, CDMX")` retorna lat/lng válidos
- [ ] `validate_address("Dirección inválida 99999")` retorna valid = false
- [ ] `calculate_distance(origen, destino)` retorna km correctos
- [ ] `ProviderDB` tiene lat/lng/service_area_km para los 8 providers
- [ ] `search_providers` con user_lat/user_lng ordena resultados por distancia + trust_score
- [ ] `create_escrow_booking` acepta y persiste dirección estructurada
- [ ] `check_in_provider` registra coordenadas reales
- [ ] Tests pasan con y sin GOOGLE_API_KEY (mock)
- [ ] Todos los tests existentes siguen pasando
