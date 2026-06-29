# HogarConfianza — Antigravity Project Context

## Project Overview
Multi-agent ADK system for connecting homes with verified service providers in Mexico. Uses Streamlit for web UI, FastAPI for API, SQLite/PostgreSQL for persistence.

## Tech Stack
- Python 3.12+, ADK 2.0 (google-adk), Streamlit, FastAPI
- SQLModel (SQLAlchemy + Pydantic) for data layer
- SQLite (dev), PostgreSQL/Cloud SQL (prod via DATABASE_URL)

## Agent Architecture
RootAgent → triage_agent → matching_agent → booking_agent → safety_agent
SecurityScreen (PII redaction + injection detection) runs as before_model_callback.

## Development Commands
- `make install` — install deps
- `streamlit run app.py` — run web UI
- `python run.py` — run CLI chat
- `python -m pytest tests/ -v` — run tests
- `agents-cli lint` — code quality checks

## Deploy
- Cloud Run: `gcloud run deploy` with DATABASE_URL pointing to Cloud SQL PostgreSQL
- Container: `docker build -t hogar-confianza . && docker run -p 8080:8080 hogar-confianza`

## Coding Standards
- Type hints required for all function signatures
- Tests must use SQLite :memory: (autouse fixture in conftest.py)
- Tool functions return JSON strings (ADK convention)
- No hardcoded secrets — use .env for API keys
