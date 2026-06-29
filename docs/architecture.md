# Diseño de Arquitectura: HogarConfianza

## Technical Approach

Sistema multi-agente con Google ADK donde un RootAgent orquesta 4 sub-agentes especializados. Cada sub-agente tiene herramientas específicas y una instrucción de sistema definida. La seguridad (PII redaction + detección de prompt injection) se ejecuta como `before_model_callback` antes de que cualquier mensaje llegue al LLM. La API expone endpoints REST via FastAPI y un servidor MCP para catálogo de servicios.

---

## Architecture Decisions

### Decisión: ADK Multi-Agent con sub-agents fijos

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Sub-agents fijos en RootAgent | Routing explícito, el LLM decide a quién transferir | ✅ Elegido — simple, alinea con ADK design |
| Agentes dinámicos registrados vía MCP | Más flexible pero complejidad adicional | ❌ Descartado — overengineering para el alcance actual |

**Rationale**: ADK maneja el routing entre sub-agents nativamente. El RootAgent tiene una instrucción clara de cuándo transferir a cada sub-agent. No necesitamos un router adicional.

---

### Decisión: Seguridad en before_model_callback

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| Callback pre-LLM | PII redactado ANTES de que el modelo lo vea | ✅ Elegido — defense-in-depth |
| Post-LLM en respuesta | El modelo ya vió los datos | ❌ Descartado — viola privacidad |

**Rationale**: El `before_model_callback` de ADK permite interceptar el mensaje del usuario antes de que el LLM lo procese. Redactamos PII y detectamos injection en ese punto. Si se detecta injection, devolvemos una respuesta de seguridad sin involucrar al LLM.

---

### Decisión: In-memory para datos (sin DB real)

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| In-memory (dicts) | Sin persistencia, datos de ejemplo | ✅ Elegido — MVP / Capstone |
| SQLite / PostgreSQL | Persistencia real, migraciones | ❌ Descartado — alcance del curso |

**Rationale**: Es un capstone de 5 días. Los providers son datos mock, las reservas viven en un dict en memoria. Suficiente para demostrar el flujo completo.

---

### Decisión: HITL (Human-in-the-Loop) para pagos

**Choice**: El booking_agent requiere aprobación explícita del usuario para crear reservas y liberar pagos
**Rationale**: El escrow retiene el pago 48h post-servicio. La liberación requiere doble confirmación (usuario + proveedor). Esto es un requisito funcional del dominio (seguridad financiera).

---

## Data Flow

```ascii
Usuario ──→ FastAPI /chat ──→ before_model_callback
                                        │
                                  SecurityScreen
                                  (PII redaction
                                   + injection check)
                                        │
                            ┌───────────┴───────────┐
                            ↓                       ↓
                      injection?                 safe
                            │                       │
                     return block           RootAgent (LLM)
                                                    │
                                          ┌─────────┼─────────┐
                                          ↓         ↓         ↓
                                    Triage → Matching → Safety
                                          ↓         ↓
                                       Booking ←──┘
                                                    │
                                            create_escrow_booking
                                                    │
                                            HITL approve/reject
                                                    │
                                            release_payment
                                                    │
                                              FastAPI Response
                                                    │
                                              Usuario ←────────
```

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI (fast_api_app.py)             │
│  POST /chat │ POST /trigger/pubsub │ GET /health        │
│  ADK Runner (InMemorySessionService)                    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              RootAgent (agent.py)                        │
│  • before_model_callback → SecurityScreen               │
│  • Instrucción: orquestación + reglas de seguridad      │
│  • Sub-agents: triage, matching, safety, booking        │
└────┬─────────┬──────────┬──────────┬────────────────────┘
     │         │          │          │
     ▼         ▼          ▼          ▼
┌────────┐┌────────┐┌─────────┐┌──────────┐
│Triage  ││Matching││ Safety  ││ Booking  │
│(clasi-  ││(buscar ││(check-  ││(escrow,  │
│ficar   ││+ veri- ││in/out,  ││ HITL,    │
│servicio││ficar)  ││pánico)  ││release)  │
└────────┘└───┬────┘└────┬────┘└────┬─────┘
              │          │          │
              ▼          ▼          ▼
       ┌──────────┐┌──────────┐┌──────────┐
       │Provider  ││ Safety   ││Provider  │
       │Tools     ││ Tools    ││Tools     │
       │(search,  ││(check-in,││(escrow,  │
       │verify,   ││ panic,   ││ approve, │
       │details)  ││ incident)││ release) │
       └──────────┘└──────────┘└──────────┘

┌─────────────────────────────────────────────────────────┐
│              MCP Server (mcp_server/server.py)           │
│  • get_service_info → catálogo de servicios             │
│  • get_safety_tips → consejos de seguridad              │
│  • list_service_categories → categorías disponibles     │
└─────────────────────────────────────────────────────────┘
```

---

## Module Map

| Archivo | Rol |
|---------|-----|
| `hogar_confianza/agent.py` | RootAgent + SecurityScreen callback |
| `hogar_confianza/fast_api_app.py` | FastAPI entry point (ADK Runner) |
| `hogar_confianza/agents/triage.py` | Clasificador de servicios |
| `hogar_confianza/agents/matching.py` | Matching + verificación |
| `hogar_confianza/agents/safety.py` | Seguridad durante servicio |
| `hogar_confianza/agents/booking.py` | Escrow + HITL |
| `hogar_confianza/tools/provider_tools.py` | 8 tools: search, verify, escrow, approve, reject, release |
| `hogar_confianza/tools/safety_tools.py` | 5 tools: check-in/out, notify, panic, incident |
| `hogar_confianza/models/schemas.py` | Pydantic models: ServiceType, Provider, Booking, SafetyCheckIn |
| `hogar_confianza/security/pii_redactor.py` | SecurityScreen: PII redaction + injection detection |
| `hogar_confianza/mcp_server/server.py` | Servidor MCP (catálogo + safety tips) |
| `run.py` | CLI interactivo (ADK Runner) |
| `app.py` | Streamlit web UI (chat + cards + dashboard) |
| `hogar_confianza/database/engine.py` | Conexión DB: SQLite (dev) / PostgreSQL (Cloud Run vía DATABASE_URL) |
| `hogar_confianza/database/models.py` | SQLModel: ProviderDB, BookingDB, SafetyCheckInDB |
| `hogar_confianza/database/seed.py` | Seed de 8 providers |
| `.agents/CONTEXT.md` | Contexto para Antigravity IDE |
| `Dockerfile` | Multi-stage build para Cloud Run |
| `tests/test_agents.py` | 8 tests unitarios |
| `tests/test_database.py` | 14 tests DB |
| `tests/test_tools_db.py` | 18 tests tools |
| `tests/conftest.py` | Fixtures: DB :memory: autouse |
| `tests/eval/` | Eval framework con LLM-as-judge |

---

## Web UI Architecture (Streamlit)

```
Usuario (Browser) ←→ Streamlit (app.py)
                          │
                    ADK Runner (singleton, asyncio.run)
                          │
                    RootAgent → triage → matching → booking → safety
                          │
                    SecurityScreen (PII + injection)
                          │
                    SQLite / PostgreSQL
```

### Pages / Components
- **Chat principal** — historial de mensajes con detección de JSON (cards de proveedores, info de booking)
- **Sidebar** — registro de usuario, reservas activas con check-in/out, botón de pánico
- **session_state** — userName, userPhone, messages[], selectedProvider

---

## Cloud Run Deploy

```
Dockerfile (multi-stage)
  → builder (install deps)
  → runtime (slim, solo site-packages + app)
  → CMD: streamlit run app.py --port 8080
```

| Variable | Dev | Cloud Run |
|----------|-----|-----------|
| `DATABASE_URL` | No set → SQLite | PostgreSQL (Cloud SQL) |
| `PORT` | 8501 (default Streamlit) | 8080 (Cloud Run) |

---

## Antigravity IDE Setup

```
.agents/
└── CONTEXT.md    ← Reglas de proyecto, tech stack, comandos
```

El proyecto es compatible con `agents-cli`:
- `agents-cli lint` → Ruff checks
- `agents-cli deploy` → Cloud Run
- `agents-cli run` → Probar agente

---

## Security Architecture

```
User Input
    │
    ▼
┌──────────────────────────────────────┐
│ SecurityScreen.process()             │
│  1. redact_pii()                     │
│     • PHONE, EMAIL, CREDIT_CARD      │
│     • CURP (México)                  │
│     • PHONE_MX_DIRECT (10 dígitos)   │
│     • ADDRESS_DETAIL (calle + nombre)│
│  2. detect_prompt_injection()        │
│     • 8 regex patterns               │
│     • "ignora instrucciones"         │
│     • "auto-aprueba sin revisión"    │
│     • "olvida las reglas"            │
│  3. Return: safe_to_proceed?         │
└──────────────────────────────────────┘
    │
    ▼
RootAgent (LLM) ← sólo si safe_to_proceed
```

---

## Testing Strategy

| Capa | Qué | Cómo |
|------|-----|------|
| Unit | PII redaction (CURP, phone, email, clean input) | pytest directo a SecurityScreen |
| Unit | Injection detection (bypass, olvida, auto-aprueba) | pytest con patrones conocidos |
| Unit | DB engine (get_engine_url, memory vs file, DATABASE_URL) | pytest parametrized con monkeypatch |
| Unit | Provider tools (search, verify, create escrow) | pytest con SQLite :memory: |
| Unit | Safety tools (check-in, check-out, DB update) | pytest con SQLite :memory: |
| Eval | 8 escenarios end-to-end con LLM-as-judge | generate_traces.py → evaluate.py |
| Eval | Métricas: routing, security, safety | Scores 1-5 por escenario |

---

## Open Questions

- [x] Migrar a base de datos real (SQLite para dev, PostgreSQL para prod) → ✅ DATABASE_URL env var
- [x] Agregar linter + formatter (ruff) al pipeline → ✅ ruff config + agents-cli lint
- [ ] Agregar autenticación de usuarios (JWT / sesiones)?
- [ ] Rate limiting en /chat endpoint?
- [ ] Integración con pasarela de pago real (Stripe / Conekta)?
