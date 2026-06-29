# Database Persistence Specification

## Purpose

Almacenamiento persistente con SQLite + SQLModel para providers, bookings y check-ins. Los datos deben sobrevivir reinicios de la aplicación.

## Requirements

### Requirement: Provider Data Persistence

The system MUST persist provider data in SQLite and MUST seed 8 providers on first run.

#### Scenario: Providers available after restart

- GIVEN la aplicación se inicia por primera vez
- WHEN se ejecuta el seed
- THEN existen 8 providers en la DB con datos completos (id, name, service, rating, verified, zip_codes, phone, years_experience, has_insurance, completed_jobs, trust_score)

#### Scenario: Search providers from DB

- GIVEN providers sembrados en SQLite
- WHEN `search_providers("plomeria", "06600")` es llamado
- THEN retorna solo providers con service=plomeria Y "06600" en zip_codes

#### Scenario: Fallback por código postal

- GIVEN providers sembrados en SQLite
- WHEN `search_providers("plomeria", "99999")` es llamado (zip_code sin cobertura)
- THEN retorna providers con service=plomeria (sin filtro de zip_code)

### Requirement: Provider Details and Verification

The system MUST retrieve provider details and run background verification from SQLite.

#### Scenario: Get provider details by ID

- GIVEN un provider existe en SQLite
- WHEN `get_provider_details("PROV-001")` es llamado
- THEN retorna todos los campos del provider incluyendo trust_score, verified, has_insurance

#### Scenario: Provider not found

- GIVEN un provider ID no existe en SQLite
- WHEN `get_provider_details("PROV-999")` es llamado
- THEN retorna `{"error": "Proveedor no encontrado"}`

#### Scenario: Background verification

- GIVEN un provider existe en SQLite con verified=True, trust_score=4.7, has_insurance=True
- WHEN `verify_provider_background("PROV-001")` es llamado
- THEN retorna `verification_status: "APROBADO"` sin issues

#### Scenario: Background verification fails

- GIVEN un provider con verified=False, trust_score=3.2, has_insurance=False
- WHEN `verify_provider_background("PROV-007")` es llamado
- THEN retorna `verification_status: "REQUIERE_REVISION"` con issues listando problemas

### Requirement: Escrow Booking Lifecycle

The system MUST manage the full booking lifecycle in SQLite: PENDIENTE_APROBACION → CONFIRMADA → COMPLETADA, o RECHAZADA.

#### Scenario: Create escrow booking

- GIVEN un provider existe en SQLite
- WHEN `create_escrow_booking` es llamado con datos válidos
- THEN se crea un registro en la tabla Booking con status "PENDIENTE_APROBACION" y escrow_held=False
- AND retorna booking_id, status y mensaje con monto retenido

#### Scenario: Approve booking

- GIVEN un booking existe con status "PENDIENTE_APROBACION"
- WHEN `approve_booking(booking_id)` es llamado
- THEN el booking cambia a status "CONFIRMADA" y escrow_held=True

#### Scenario: Reject booking

- GIVEN un booking existe con status "PENDIENTE_APROBACION"
- WHEN `reject_booking(booking_id)` es llamado
- THEN el booking cambia a status "RECHAZADA" y escrow_held=False

#### Scenario: Release payment with dual confirmation

- GIVEN un booking existe con status "CONFIRMADA"
- WHEN `release_payment(booking_id, provider_confirmed=True, user_confirmed=True)` es llamado
- THEN el booking cambia a status "COMPLETADA" y escrow_held=False

#### Scenario: Release payment blocked without dual confirmation

- GIVEN un booking existe con status "CONFIRMADA"
- WHEN `release_payment(booking_id, provider_confirmed=False, user_confirmed=True)` es llamado
- THEN la API retorna status "RETENIDO" y el booking permanece con status "CONFIRMADA" en DB

#### Scenario: Booking not found

- GIVEN un booking ID no existe
- WHEN `approve_booking("BK-999")` es llamado
- THEN retorna `{"error": "Reserva no encontrada"}`

### Requirement: Safety Check-In/Out

The system MUST persist safety check-in and check-out events in SQLite.

#### Scenario: Provider check-in

- GIVEN un booking confirmado existe en SQLite
- WHEN `check_in_provider(booking_id, provider_name, location)` es llamado
- THEN se crea un registro SafetyCheckIn con check_in_time, selfie_confirmed=True, location_verified=True, trusted_contact_notified=True

#### Scenario: Provider check-out

- GIVEN un SafetyCheckIn existe con check_out_time=None
- WHEN `check_out_provider(booking_id, provider_name, hours_worked)` es llamado
- THEN se actualiza el registro con check_out_time y hours_worked

### Requirement: Database Connection

The system MUST use a single SQLite database file for production and `:memory:` for tests.

#### Scenario: Production database file

- GIVEN la aplicación se inicia en modo producción
- WHEN se crea el engine
- THEN el archivo `hogar_confianza.db` existe en el directorio del proyecto

#### Scenario: Test database in memory

- GIVEN los tests se ejecutan
- WHEN se crea el engine
- THEN usa `sqlite:///:memory:` y no deja archivos residuales
