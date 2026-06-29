# Proposal: Migración a SQLite

## Intent

Reemplazar el almacenamiento in-memory (dicts) por SQLite con SQLModel. Providers, bookings, escrows y sesiones deben persistir entre reinicios de la aplicación. La API de las tools no cambia — solo el backend de datos.

## Scope

### In Scope
- Definir modelos SQLModel (Provider, Booking, ServiceRequest, SafetyCheckIn)
- Reemplazar `_PROVIDERS_DB` estático por tabla SQLite con seed data
- Reemplazar `_ESCROW_DB` dict por tabla Booking con estados
- Agregar sesiones persistentes (reemplazar InMemorySessionService)
- Migrar `provider_tools.py` y `safety_tools.py` a usar DB
- Script de seed con los 8 providers existentes
- Tests existentes deben seguir pasando

### Out of Scope
- PostgreSQL u otra DB externa (se puede cambiar después con la connection string)
- ORM avanzado o migraciones Alembic (SQLModel create_all es suficiente para ahora)
- UI de admin para ver datos
- Autenticación de usuarios

## Capabilities

### New Capabilities
- `database-persistence`: Almacenamiento persistente con SQLite + SQLModel

### Modified Capabilities
- None (no existing specs to modify)

## Approach

1. Agregar `sqlmodel` a dependencias en `pyproject.toml`
2. Crear `hogar_confianza/database/` con:
   - `engine.py` — creación de engine + sesión
   - `models.py` — modelos SQLModel (Provider, Booking)
   - `seed.py` — datos iniciales de providers
3. Refactor `tools/provider_tools.py`:
   - `search_providers` → query SQLite
   - `get_provider_details` → query por ID
   - `verify_provider_background` → query por ID
   - `create_escrow_booking` → INSERT en Booking
   - `approve_booking` / `reject_booking` / `release_payment` → UPDATE estados
4. Refactor `tools/safety_tools.py`:
   - `check_in_provider` / `check_out_provider` → INSERT/UPDATE en SafetyCheckIn
5. Sesiones: evaluar si usamos SQLite también o dejamos InMemorySessionService de ADK
6. Tests: actualizar mocks para usar DB en memoria (SQLite `:memory:`)

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `pyproject.toml` | Modified | Agregar sqlmodel dependency |
| `hogar_confianza/database/` | New | engine.py, models.py, seed.py |
| `hogar_confianza/tools/provider_tools.py` | Modified | De dict a SQLite queries |
| `hogar_confianza/tools/safety_tools.py` | Modified | De respuesta estática a DB |
| `hogar_confianza/models/schemas.py` | Modified | Adaptar a SQLModel (opcional) |
| `hogar_confianza/fast_api_app.py` | Modified | Session service persistence |
| `run.py` | Modified | Session service persistence |
| `tests/test_agents.py` | Modified | Usar `:memory:` DB |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Romper tools existentes | Medium | Tests primero (TDD), mantener API de tools idéntica |
| Session service de ADK no soporta SQLite fácil | Medium | Evaluar si vale la pena o dejamos InMemorySessionService |

## Rollback Plan

Volver al commit anterior. La API pública (firmas de tools, endpoints) NO cambia.

## Dependencies

- `sqlmodel` (PyPI)

## Success Criteria

- [ ] `make test` pasa todos los tests
- [ ] Datos de providers persisten entre reinicios de `run.py`
- [ ] Reservas creadas persisten entre reinicios
- [ ] Seed data de 8 providers disponible al iniciar
