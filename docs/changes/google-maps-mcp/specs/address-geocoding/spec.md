# Address Geocoding Specification

## Purpose

Proveer geocoding y validación de direcciones para domicilios de usuarios usando Google Maps API, expuesto como MCP server y como tools de ADK agents. Permitir que los agents trabajen con coordenadas reales para matching, check-in y notificaciones.

## Requirements

### Requirement: Geocode Address

The system MUST convert a human-readable address string to geographic coordinates and structured components.

#### Scenario: Geocode a complete address in Mexico

- GIVEN una dirección válida en México
- WHEN `geocode_address("Av. Reforma 222, Col. Juárez, Cuauhtémoc, CDMX, 06600")` es llamado
- THEN retorna un objeto con lat, lng, formatted_address, y address_components
- AND lat/lng están dentro del rango de CDMX (~19.4, -99.1)

#### Scenario: Geocode with partial address

- GIVEN una dirección parcial como "Av. Reforma, CDMX"
- WHEN `geocode_address` es llamado
- THEN retorna el mejor match con lat/lng y formatted_address completa
- AND confidence indica que es parcial

#### Scenario: Geocode non-existent address

- GIVEN una dirección que no existe
- WHEN `geocode_address("Calle Falsa 99999, Colonia Inexistente, XYZ")` es llamado
- THEN retorna resultados_geocoding como arreglo vacío
- AND un mensaje indicando que no se encontró la dirección

#### Scenario: Geocode without API key (mock mode)

- GIVEN que GOOGLE_API_KEY no está configurada
- WHEN `geocode_address` es llamado
- THEN retorna datos mock con lat/lng simulados
- AND un flag `mock: true` indicando que no son datos reales

### Requirement: Validate Address

The system MUST validate whether an address exists and provide suggestions.

#### Scenario: Validate a valid address

- GIVEN una dirección válida y completa
- WHEN `validate_address` es llamado
- THEN retorna `valid: true` y la dirección formateada por Google

#### Scenario: Validate an invalid address

- GIVEN una dirección que no existe
- WHEN `validate_address` es llamado
- THEN retorna `valid: false` y sugerencias de corrección

#### Scenario: Validate with ambiguous address

- GIVEN una dirección ambigua tipo "Calle 5 de Mayo"
- WHEN `validate_address` es llamado
- THEN retorna `valid: true, ambiguous: true`
- AND una lista de posibles matches con ciudad/colonia

### Requirement: Calculate Distance

The system MUST calculate distance between two addresses or coordinates.

#### Scenario: Calculate distance between two addresses

- GIVEN dos direcciones válidas
- WHEN `calculate_distance("Av. Reforma 222, CDMX", "Coyoacán, CDMX")` es llamado
- THEN retorna distance_km (número positivo)
- AND duration_minutes estimado

#### Scenario: Calculate distance between coordinates

- GIVEN dos pares de lat/lng
- WHEN `calculate_distance` es llamado con coordenadas
- THEN retorna la distancia en km usando la fórmula de Haversine (sin API key) o Google Distance Matrix (con key)

### Requirement: Search Places

The system MUST provide place autocomplete/search for address input.

#### Scenario: Search places with query

- GIVEN un query parcial como "Reforma 222"
- WHEN `search_places("Reforma 222, CDMX")` es llamado
- THEN retorna una lista de matches con place_id, description, y lat/lng

#### Scenario: Search places restricted to Mexico

- GIVEN un query
- WHEN `search_places` es llamado
- THEN los resultados están restringidos a México (componentes de país)

### Requirement: Address Persistence

The system MUST store structured addresses linked to bookings.

#### Scenario: Create booking with address

- GIVEN un usuario con dirección validada
- WHEN `create_escrow_booking` es llamado con address_id o dirección embebida
- THEN se guarda la dirección estructurada en la tabla user_addresses
- AND la booking referencia esa dirección

#### Scenario: Reuse address across bookings

- GIVEN un usuario que ya registró su dirección
- WHEN hace una segunda reserva
- THEN puede reusar la dirección existente sin re-geocoding

### Requirement: Safety Check-in with Coordinates

The system MUST use real coordinates for safety check-in.

#### Scenario: Provider check-in with geocoded address

- GIVEN una booking con dirección geocodificada
- WHEN `check_in_provider` es llamado
- THEN el registro SafetyCheckIn incluye las coordenadas del domicilio
- AND location_verified usa las coordenadas reales

#### Scenario: Panic button with structured address

- GIVEN una emergencia durante un servicio
- WHEN `trigger_panic_button` es llamado
- THEN la alerta incluye dirección estructurada completa y coordenadas
