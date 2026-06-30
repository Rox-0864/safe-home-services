# Design: Google Maps MCP Integration for Addresses

## Technical Approach

Servidor MCP autónomo para Google Maps + Python tools para ADK agents. La capa de Google Maps API se abstrae en un cliente interno (`maps_client.py`) que maneja autenticación, errores y modo mock. Los agents de ADK llaman a las tools directamente; el MCP server expone la misma funcionalidad para consumo externo.

## Architecture Decisions

### Decision: MCP server separado del de catálogo

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| MCP server separado (`maps_server.py`) | Un server más, pero dominio separado | ✅ Elegido — Google Maps es un dominio distinto a catálogo/safety tips |
| Tools en el MCP server existente | Menos servers, pero mezcla dominios | ❌ Descartado — viola separación de concerns |

### Decision: `requests` directo vs `google-maps-services-python`

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| `requests` directo a REST API | Sin dependencia extra, control total | ✅ Elegido — liviano, sin abstracción que esconda errores |
| `google-maps-services-python` | Tipado, retry, rate limiting built-in | ❌ Descartado — dependencia pesada para 4-5 calls |

### Decision: Mock mode cuando no hay API key

- **Elegido**: Si `GOOGLE_API_KEY` no está configurada, las tools retornan datos mock con `mock: true`
- **Rationale**: El API key está bloqueada. Necesitamos poder desarrollar y testear sin depender de Google. El mock es explícito (flag) para que el agente sepa que no son datos reales
- **Mock data**: Proveedores distribuidos en distintas colonias de CDMX (Centro, Roma, Condesa, Del Valle, Coyoacán, Polanco, Narvarte, Escandón)

### Decision: Dirección embebida en Booking vs FK a UserAddress

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| FK a UserAddress table | Normalizado, reutilizable | ✅ Elegido — permite reusar dirección entre bookings |
| Dirección embebida en Booking | Sin join, pero duplicación | ❌ Descartado — el usuario puede tener múltiples bookings en la misma dirección |

### Decision: Coordenadas en ProviderDB vs tabla separada

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Campos `lat`, `lng`, `service_area_km` en ProviderDB | Un campo más en la tabla existente, simple | ✅ Elegido — los providers no cambian de dirección, no justifica otra tabla |
| `ProviderAddressDB` con FK | Normalizado, pero over-engineering | ❌ Descartado — los providers son datos semilla, no mutan |

### Decision: Orden de resultados en search_providers

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Ordenar por distancia × trust_score (ponderado) | Balancea calidad + cercanía | ✅ Elegido — el mejor provider cerca del usuario |
| Solo distancia | Ignora calidad | ❌ Descartado — un provider malo pero cercano no sirve |
| Solo trust_score (status quo) | Ignora ubicación | ❌ Descartado — no aprovecha las coordenadas |

### Decision: Cache de geocoding en memoria

- **Elegido**: Dict simple en maps_client.py con TTL de 1 hora
- **Rationale**: Un usuario no cambia de dirección frecuentemente. Evita calls repetidos a la API de Google durante la misma sesión

## Data Model

### New: UserAddressDB

```python
class UserAddressDB(SQLModel, table=True):
    __tablename__ = "user_addresses"

    id: str = Field(primary_key=True)
    user_id: str
    calle: str
    numero_exterior: str | None = None
    numero_interior: str | None = None
    colonia: str
    ciudad: str
    estado: str
    zip_code: str
    pais: str = "México"
    lat: float | None = None
    lng: float | None = None
    formatted_address: str | None = None
    place_id: str | None = None
    is_verified: bool = False
    created_at: str
```

### Modified: ProviderDB

```python
class ProviderDB(SQLModel, table=True):
    __tablename__ = "providers"

    id: str = Field(primary_key=True)
    name: str
    service: str
    rating: float
    verified: bool
    zip_codes: list[str] = Field(default_factory=list, sa_type=JSON)
    phone: str
    years_experience: int
    has_insurance: bool
    completed_jobs: int
    trust_score: float
    # nuevos campos:
    lat: float | None = None
    lng: float | None = None
    service_area_km: float = 10.0  # radio de cobertura por defecto
    address_formatted: str | None = None
```

### Modified: BookingDB

```python
class BookingDB(SQLModel, table=True):
    __tablename__ = "bookings"
    # ... campos existentes ...
    address_id: str | None = Field(default=None, foreign_key="user_addresses.id")
```

### New: Address Pydantic Schema

```python
class Address(BaseModel):
    calle: str
    numero_exterior: Optional[str] = None
    numero_interior: Optional[str] = None
    colonia: str
    ciudad: str
    estado: str
    zip_code: str
    pais: str = "México"
    lat: Optional[float] = None
    lng: Optional[float] = None
    formatted_address: Optional[str] = None
```

### Provider Seed Data (CDMX)

Los 8 providers existentes se distribuyen en distintas colonias de CDMX para que el matching por distancia sea significativo:

| ID | Nombre | Colonia | lat | lng |
|----|--------|---------|-----|-----|
| PROV-001 | María García | Roma Norte | 19.419 | -99.163 |
| PROV-002 | Juan Pérez | Del Valle Centro | 19.386 | -99.169 |
| PROV-003 | Laura Martínez | Condesa | 19.413 | -99.176 |
| PROV-004 | Carlos López | Polanco | 19.433 | -99.191 |
| PROV-005 | Ana Rodríguez | Narvarte | 19.396 | -99.143 |
| PROV-006 | Roberto Sánchez | Escandón | 19.407 | -99.188 |
| PROV-007 | Patricia Morales | Coyoacán Centro | 19.350 | -99.162 |
| PROV-008 | Fernando Castillo | San Pedro Tláhuac | 19.295 | -99.056 |

## Component Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     maps_client.py                                │
│  • GoogleMapsClient class                                        │
│  • __init__(api_key, mock_mode)                                  │
│  • geocode(address) → GeocodingResult                            │
│  • reverse_geocode(lat, lng) → GeocodingResult                   │
│  • distance_matrix(origin, dest) → DistanceResult                 │
│  • places_autocomplete(query) → list[PlaceSuggestion]            │
│  • Cache interno (dict, 1h TTL)                                  │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ├────────────────────────────────┐
       │                                │
       ▼                                ▼
┌──────────────┐               ┌──────────────────┐
│ maps_tools.py │               │ maps_server.py   │
│ (ADK tools)   │               │ (MCP server)     │
│               │               │                  │
│ geocode_      │               │ geocode_address  │
│  address()    │               │ validate_address │
│ validate_     │               │ calc_distance    │
│  address()    │               │ search_places    │
│ calc_distance │               └──────────────────┘
│ search_places │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│  ADK Agents (via tool binding)                                   │
│                                                                  │
│  matching_agent:                                                 │
│    1. geocode_address(direccion_usuario) → user_lat, user_lng     │
│    2. search_providers(servicio, cp, user_lat, user_lng)          │
│       → providers ordenados por score_distancia                   │
│    3. calculate_distance(provider_coords, user_coords)            │
│       → muestra al usuario la distancia exacta                    │
│                                                                  │
│  safety_agent:    geocode_address → coordenadas para check-in    │
│                   validate_address → verifica domicilio antes    │
│                                      de notificar                │
└──────────────────────────────────────────────────────────────────┘
```

## API Design

### Tool: `geocode_address`

```
Input:  { "address": "Av. Reforma 222, Col. Juárez, CDMX, 06600" }
Output: {
  "success": true,
  "result": {
    "lat": 19.426,
    "lng": -99.158,
    "formatted_address": "Av. Paseo de la Reforma 222, Juárez, 06600 Ciudad de México, CDMX, Mexico",
    "components": {
      "street": "Av. Paseo de la Reforma",
      "number": "222",
      "neighborhood": "Juárez",
      "city": "Ciudad de México",
      "state": "Ciudad de México",
      "zip": "06600",
      "country": "México"
    },
    "place_id": "ChIJ..."
  },
  "mock": false
}
```

### Tool: `validate_address`

```
Input:  { "address": "Calle 123, Colonia Centro, CDMX" }
Output: {
  "success": true,
  "valid": true,
  "formatted_address": "Calle 123, Centro, 06000 Ciudad de México, CDMX, Mexico",
  "suggestions": []
}
```

### Tool: `calculate_distance`

```
Input:  {
  "origin": { "lat": 19.426, "lng": -99.158 },
  "destination": { "lat": 19.350, "lng": -99.067 }
}
Output: {
  "success": true,
  "distance_km": 12.4,
  "duration_minutes": 25,
  "mode": "driving",
  "mock": false
}
```

### Tool: `search_places`

```
Input:  { "query": "Reforma 222, CDMX" }
Output: {
  "success": true,
  "results": [
    {
      "place_id": "ChIJ...",
      "description": "Av. Paseo de la Reforma 222, Juárez, 06600 CDMX",
      "lat": 19.426,
      "lng": -99.158
    }
  ]
}
```

### Modified: `search_providers` (ADK tool)

Ahora acepta `user_lat` y `user_lng` opcionales. Cuando se proveen, los resultados incluyen `distance_km` y se ordenan por un score ponderado (trust_score × 0.6 + cercanía × 0.4).

```
Input: {
  "service_type": "plomeria",
  "zip_code": "06600",
  "user_lat": 19.419,
  "user_lng": -99.163
}
Output: [
  {
    "id": "PROV-003",
    "name": "Laura Martínez",
    "service": "plomeria",
    "trust_score": 4.8,
    "lat": 19.413,
    "lng": -99.176,
    "distance_km": 2.1,
    "within_service_area": true
  },
  ...
]
```

### New: `get_provider_location` (ADK tool)

Devuelve la ubicación almacenada de un proveedor.

```
Input:  { "provider_id": "PROV-001" }
Output: {
  "provider_id": "PROV-001",
  "name": "María García",
  "lat": 19.419,
  "lng": -99.163,
  "service_area_km": 10.0,
  "address": "Col. Roma Norte, CDMX"
}
```

## Mock Mode

Cuando `GOOGLE_API_KEY` no está configurada:

- `geocode_address`: retorna coordenadas mock del centro de CDMX (19.4326, -99.1332)
- `validate_address`: retorna `valid: true` con mock formatted_address
- `calculate_distance`: usa fórmula de Haversine directa (no necesita API key)
- `search_places`: retorna 2-3 places mock
- `search_providers`: retorna datos reales de DB siempre (no mock), con `distance_km` calculado via Haversine
- `get_provider_location`: retorna datos reales de DB
- Todos los resultados de geocoding incluyen `mock: true`

## Environment

```
# .env
GOOGLE_API_KEY=AIza...  # opcional, si no está → modo mock
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `hogar_confianza/mcp_server/maps_server.py` | Create | MCP server con tools de geocoding |
| `hogar_confianza/tools/maps_client.py` | Create | Cliente HTTP para Google Maps API + cache |
| `hogar_confianza/tools/maps_tools.py` | Create | Python functions para ADK agents |
| `hogar_confianza/database/models.py` | Modify | +UserAddressDB, +ProviderDB.lat/lng/service_area, +BookingDB.address_id |
| `hogar_confianza/database/seed.py` | Modify | +coordenadas reales para los 8 providers (CDMX) |
| `hogar_confianza/database/engine.py` | Modify | Migración: crear tabla user_addresses |
| `hogar_confianza/models/schemas.py` | Modify | +Address, +Provider.lat/lng/service_area |
| `hogar_confianza/tools/provider_tools.py` | Modify | search_providers con distancia, get_provider_location, create_escrow_booking con address |
| `hogar_confianza/tools/safety_tools.py` | Modify | check_in/out con lat/lng |
| `hogar_confianza/agents/matching.py` | Modify | +maps_tools, ordenar providers por cercanía |
| `hogar_confianza/agents/safety.py` | Modify | +maps_tools, verificar ubicación |
| `hogar_confianza/i18n.py` | Modify | +prompts de dirección + distancia para agents |
| `pyproject.toml` | Modify | +requests dependency |
| `.env.example` | Modify | +GOOGLE_API_KEY |
| `tests/test_maps_tools.py` | Create | Tests para maps_tools |
| `tests/test_maps_client.py` | Create | Tests para maps_client (mock HTTP) |
| `tests/test_provider_location.py` | Create | Tests para búsqueda por distancia |

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Unit | maps_client geocoding | Mock `httpx.get` / `requests.get`, verify params |
| Unit | maps_client mock mode | Sin GOOGLE_API_KEY, verificar datos mock + mock flag |
| Unit | maps_tools return JSON | Verificar formato de output consistente |
| Unit | Haversine distance | Test con coordenadas conocidas (Roma → Condesa ≈ 1.5km) |
| Unit | cache hit/miss | Verificar que cache evita calls repetidos |
| Unit | Provider proximity search | search_providers con user_lat/user_lng, verificar distance_km |
| Unit | Provider ordering | search_providers ordena por score ponderado correctamente |
| Unit | Provider service area filter | Provider fuera de service_area_km marcado como within_service_area=false |
| Integration | create_escrow_booking con address | SQLite :memory: + address persistido |
| Integration | safety tools con lat/lng | Verificar coordenadas en SafetyCheckIn |
| Integration | seed con coordenadas | Verificar que los 8 providers tienen lat/lng no nulos |
