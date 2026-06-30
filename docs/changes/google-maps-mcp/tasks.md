# Tasks: Google Maps MCP Integration

## Task 1: maps_client — Google Maps API Client

**Files**: `hogar_confianza/tools/maps_client.py`

- [ ] Crear clase `GoogleMapsClient` con métodos:
  - `geocode(address: str) -> dict`
  - `reverse_geocode(lat: float, lng: float) -> dict`
  - `distance_matrix(origin: dict, destination: dict) -> dict`
  - `places_autocomplete(query: str, restrict_to_mx: bool) -> list[dict]`
- [ ] Cache en memoria con TTL 1h
- [ ] Modo mock cuando `GOOGLE_API_KEY` no está configurada
- [ ] Haversine formula para distance fallback (mock)
- [ ] Manejo de errores HTTP (timeout, 4xx, 5xx) con mensajes en español

## Task 2: maps_tools — ADK Python Tools

**Files**: `hogar_confianza/tools/maps_tools.py`

- [ ] `geocode_address(address: str) -> str` — envuelve maps_client.geocode, retorna JSON
- [ ] `validate_address(address: str) -> str` — geocoding + validación, retorna JSON con flag valid
- [ ] `calculate_distance(origin: dict, destination: dict) -> str` — retorna JSON con km y duración
- [ ] `search_places(query: str) -> str` — retorna JSON con sugerencias

## Task 3: ProviderDB — Location Fields

**Files**: `hogar_confianza/database/models.py`, `hogar_confianza/database/seed.py`

- [ ] Agregar campos a `ProviderDB`: `lat: float | None`, `lng: float | None`, `service_area_km: float = 10.0`, `address_formatted: str | None`
- [ ] Actualizar `seed.py`: asignar coordenadas reales a los 8 providers distribuidas en CDMX (Roma, Condesa, Del Valle, Polanco, Narvarte, Escandón, Coyoacán, Tláhuac)
- [ ] Verificar que los tests de seed existentes pasan

## Task 4: Data Model — UserAddressDB

**Files**: `hogar_confianza/database/models.py`, `hogar_confianza/database/engine.py`

- [ ] Crear modelo `UserAddressDB` con campos: id, user_id, calle, numero_exterior, numero_interior, colonia, ciudad, estado, zip_code, pais, lat, lng, formatted_address, place_id, is_verified, created_at
- [ ] Agregar `address_id: str | None` (FK) a `BookingDB`
- [ ] Agregar `create_tables()` en `engine.py` para migración automática de user_addresses

## Task 5: Schemas — Address Pydantic + Provider update

**Files**: `hogar_confianza/models/schemas.py`

- [ ] Crear `Address` Pydantic model (todos los campos de dirección)
- [ ] Actualizar `Provider` schema con campos `lat`, `lng`, `service_area_km`
- [ ] Actualizar `ServiceRequest` con campo `address: Address | None`
- [ ] Actualizar `Booking` con campo `address: Address | None`

## Task 6: MCP Server — maps_server.py

**Files**: `hogar_confianza/mcp_server/maps_server.py`

- [ ] Crear MCP server con tools:
  - `geocode_address`
  - `validate_address`
  - `calc_distance`
  - `search_places`
- [ ] Registrar tools con inputSchema (JSON schema)
- [ ] Integrar con `maps_client.py` para backend

## Task 7: Update provider_tools — Distance & Location

**Files**: `hogar_confianza/tools/provider_tools.py`

- [ ] `search_providers`: acepta `user_lat` y `user_lng` opcionales
  - Calcular `distance_km` desde user a cada provider vía Haversine
  - Filtrar providers fuera de `service_area_km`
  - Ordenar por score ponderado: (trust_score × 0.6) + (cercanía normalizada × 0.4)
  - Incluir `distance_km` y `within_service_area` en respuesta
- [ ] `get_provider_location(provider_id)` — retorna lat, lng, service_area_km, address
- [ ] `create_escrow_booking`: recibe parámetro `address: dict` opcional
  - Si se provee address, crear o buscar UserAddressDB y asociarlo al booking
  - Retornar address_id y dirección formateada en respuesta JSON

## Task 8: Update safety_tools

**Files**: `hogar_confianza/tools/safety_tools.py`

- [ ] `check_in_provider` acepta address_id y resuelve dirección + coordenadas
- [ ] `notify_trusted_contact` acepta address_id y usa dirección estructurada
- [ ] `trigger_panic_button` acepta address_id e incluye coordenadas en alerta

## Task 9: Agents — Tools Binding

**Files**: `hogar_confianza/agents/matching.py`, `hogar_confianza/agents/safety.py`

- [ ] `matching_agent`: agregar `maps_tools` como tools
  - Usar `geocode_address` para validar dirección del usuario ANTES de buscar
  - Usar `search_providers` con user_lat/user_lng para ordenar por cercanía
  - Usar `calculate_distance` para mostrar distancia exacta al usuario
- [ ] `safety_agent`: agregar `maps_tools` como tools
  - Usar `geocode_address` para coordenadas de check-in
  - Usar `validate_address` antes de notificar contacto de confianza

## Task 10: i18n — Agent Prompts

**Files**: `hogar_confianza/i18n.py`

- [ ] Actualizar prompt de `matching_agent`: incluir instrucción de geocodificar dirección, calcular distancia, y priorizar providers cercanos con buen trust_score
- [ ] Actualizar prompt de `safety_agent`: incluir instrucción de usar coordenadas reales y dirección estructurada
- [ ] Actualizar prompt de `root_agent`: mencionar que ahora se solicita dirección completa (calle, colonia, ciudad) para matching por cercanía

## Task 11: Config & Dependencies

**Files**: `pyproject.toml`, `.env.example`

- [ ] Agregar `requests>=2.31.0` a dependencies
- [ ] Agregar `GOOGLE_API_KEY` a `.env.example`

## Task 12: Tests

**Files**: `tests/test_maps_client.py`, `tests/test_maps_tools.py`, `tests/test_provider_location.py`

- [ ] `test_maps_client.py`:
  - Test geocode con mock HTTP
  - Test geocode en modo mock (sin API key)
  - Test reverse_geocode
  - Test distance_matrix
  - Test Haversine distance (Roma → Condesa ≈ 1.5km)
  - Test cache hit
- [ ] `test_maps_tools.py`:
  - Test `geocode_address` retorna JSON string
  - Test `validate_address` con dirección válida
  - Test `validate_address` con mock mode
  - Test `calculate_distance` con coordenadas conocidas
  - Test `search_places` en mock mode
- [ ] `test_provider_location.py`:
  - Test `search_providers` con user_lat/user_lng retorna distance_km
  - Test `search_providers` ordena por trust_score + cercanía
  - Test `search_providers` filtra providers fuera de service_area_km
  - Test `get_provider_location` retorna coordenadas del provider
  - Test que todos los providers seed tienen lat/lng no nulos

## Task 13: Verify & Lint

- [ ] Ruff: `make lint` (ruff check)
- [ ] Tests: `pytest tests/ -v` — todos pasan (incluyendo tests existentes)
- [ ] Import check: `python -c "from hogar_confianza.tools.maps_tools import geocode_address"`
