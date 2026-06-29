# Design: Web UI + Cloud Run + Antigravity

## Technical Approach

Streamlit single-process app que importa el ADK Runner directamente (sin HTTP). El agente conversacional sigue siendo el cerebro; Streamlit es solo el canal visual. Para Cloud Run: Dockerfile multi-stage con PostgreSQL support. Antigravity: directorio `.agents/` con CONTEXT.md.

## Architecture Decisions

### Decision: Streamlit single-process (no HTTP proxy)
- **Elegido**: Streamlit + ADK Runner directo — sin overhead HTTP, state management vía session_state
- **Descartado**: Streamlit → FastAPI → ADK — doble HTTP, más latencia

### Decision: DATABASE_URL env var for DB switching
- **Elegido**: DATABASE_URL env var — SQLModel/SQLAlchemy abstrae la diferencia
- **Descartado**: Build flag + config — requiere rebuild

### Decision: Streamlit session_state for user data
- **Elegido**: session_state — simple, suficiente para demo
- **Descartado**: SQLite table for users — sobreingeniería

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app.py` | Create | Entry point Streamlit: chat, cards, dashboard, check-in/out |
| `.agents/CONTEXT.md` | Create | Reglas de proyecto para Antigravity IDE |
| `Dockerfile` | Modify | Multi-stage build, entrypoint a Streamlit |
| `.dockerignore` | Create | Excluir .venv, .git, __pycache__ |
| `hogar_confianza/database/engine.py` | Modify | get_engine_url() lee DATABASE_URL |
| `Makefile` | Modify | streamlit-run, docker-build-cloud targets |
| `README.md` | Modify | Deploy Cloud Run + Antigravity + demo video |
| `pyproject.toml` | Modify | +streamlit, +ruff |
| `tests/test_database.py` | Modify | +3 tests: get_engine_url parametrized |

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Unit | get_engine_url() con/sin DATABASE_URL | pytest parametrized (3 tests) |
| Integration | 44 tests existentes pasan | pytest |
| Import | app.py importa sin errores | python3 -c "import app" |
