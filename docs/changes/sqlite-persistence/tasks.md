# Tasks: Migración a SQLite

## Phase 1: Foundation — Database Module

- [x] 1.1 Agregar `sqlmodel` a `pyproject.toml` dependencies
- [x] 1.2 Crear `hogar_confianza/database/__init__.py`
- [x] 1.3 Crear `hogar_confianza/database/engine.py` — engine + `get_session()` con soporte `:memory:` para tests
- [x] 1.4 Crear `hogar_confianza/database/models.py` — SQLModel: `ProviderDB`, `BookingDB`, `SafetyCheckInDB`
- [x] 1.5 Crear `hogar_confianza/database/seed.py` — seed de 8 providers desde datos existentes

## Phase 2: Core Implementation — Tools Migration

- [x] 2.1 Refactor `search_providers()` en `provider_tools.py` — query SQLite por service + zip_code
- [x] 2.2 Refactor `get_provider_details()` — query SQLite por provider_id
- [x] 2.3 Refactor `verify_provider_background()` — query SQLite + lógica de issues
- [x] 2.4 Refactor `create_escrow_booking()` — INSERT en BookingDB con status PENDIENTE_APROBACION
- [x] 2.5 Refactor `approve_booking()` / `reject_booking()` — UPDATE status en BookingDB
- [x] 2.6 Refactor `release_payment()` — UPDATE status a COMPLETADA con dual confirmation
- [x] 2.7 Refactor `check_in_provider()` en `safety_tools.py` — INSERT en SafetyCheckInDB
- [x] 2.8 Refactor `check_out_provider()` — UPDATE check_out_time en SafetyCheckInDB

## Phase 3: Integration

- [x] 3.1 Ejecutar `engine.init_db()` y `seed_db()` al inicio de `run.py`
- [x] 3.2 Ejecutar `engine.init_db()` y `seed_db()` al inicio de `fast_api_app.py`
- [x] 3.3 Verificar que el archivo `hogar_confianza.db` se crea al arrancar

## Phase 4: Tests

- [x] 4.1 Actualizar tests existentes para usar `:memory:` SQLite en fixture `override_get_session`
- [x] 4.2 Correr `make test` y verificar que los 8 tests + nuevos pasan
