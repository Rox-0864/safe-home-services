# 🏠 HogarConfianza — AI Concierge Agent

**Track:** Concierge Agents | **Kaggle Capstone:** 5-Day AI Agents: Intensive Vibe Coding Course With Google

[![CI](https://github.com/Rox-0864/safe-home-services/actions/workflows/ci.yml/badge.svg)](https://github.com/Rox-0864/safe-home-services/actions/workflows/ci.yml)

Conecta hogares mexicanos con proveedores de servicio doméstico **CONFIABLES y VERIFICADOS** mediante un sistema multi-agente con pagos en garantía y protocolos de seguridad.

## 🚀 Quick Start

```bash
# 1. Instalar dependencias
make install

# 2. Configurar API key
cp .env.example .env
# Editar .env con tu API key de https://aistudio.google.com/app/apikey

# 3. ¡Ejecutar!
make run
```

## 🧠 Arquitectura de Agentes

```
Usuario → RootAgent
              │
              ├── TriageAgent    → Clasifica el servicio solicitado
              ├── MatchingAgent  → Busca proveedores + verifica antecedentes
              ├── SafetyAgent    → Check-in/out, botón de pánico, contacto confianza
              └── BookingAgent   → Reserva + Escrow (pago retenido) + liberación
```

## ✅ Conceptos Demostrados

| Concepto | Implementación |
|----------|---------------|
| **Multi-Agent** | RootAgent + 4 sub-agentes especializados |
| **Tools** | 8 herramientas: búsqueda, verificación, escrow, check-in, pánico |
| **MCP** | Servidor MCP con catálogo de servicios y consejos de seguridad |
| **Seguridad** | Redacción de PII (CURP, teléfono, email) + detección de prompt injection |
| **HITL** | Aprobación humana obligatoria para reservas y liberación de pagos |
| **Memory** | Sesiones persistentes por usuario |
| **Evaluación** | 8 casos de prueba con LLM-as-judge |
| **Observabilidad** | Logging estructurado, trazabilidad de eventos |

## 🔐 Seguridad

- **PII Redaction**: CURP, teléfonos, emails, direcciones redactados antes del LLM
- **Prompt Injection**: Detección de 8 patrones de inyección conocidos
- **Escrow**: Pago retenido 48h post-servicio, liberación solo con doble confirmación
- **Botón de pánico**: Alerta inmediata a contacto de confianza + equipo de seguridad
- **Provider Vetting**: Verificación de antecedentes, seguro, trust score

## 🌐 Web UI

```bash
make streamlit-run
# Abre http://localhost:8501
```

## 🐳 Deploy Local

```bash
make docker-build
make docker-run
```

## ☁️ Deploy a Cloud Run

```bash
# 1. Build y push a Container Registry
make docker-build-cloud

# O manualmente:
docker build -t gcr.io/$(gcloud config get-value project)/hogar-confianza .
docker push gcr.io/$(gcloud config get-value project)/hogar-confianza

# 2. Crear secret con DATABASE_URL (Cloud SQL PostgreSQL)
echo -n "postgresql://user:pass@host/db" | \
  gcloud secrets create hogar-confianza-db-url --data-file=-

# 3. Deploy
gcloud run deploy hogar-confianza \
  --image gcr.io/$(gcloud config get-value project)/hogar-confianza \
  --port 8080 \
  --set-env-vars "DATABASE_URL=$(gcloud secrets versions access latest --secret=hogar-confianza-db-url)"
```

> **Nota**: Sin `DATABASE_URL`, la app usa SQLite local (útil para dev pero NO para Cloud Run, cuyo filesystem es efímero).

## 🤖 Antigravity IDE

El proyecto incluye estructura `.agents/` para Google Antigravity IDE. Abrí el proyecto en Antigravity y:

```bash
# Verificar configuración
agents-cli info

# Lint
agents-cli lint

# Ejecutar tests
python -m pytest tests/ -v

# Correr web UI
streamlit run app.py
```

## 📹 Demo Video — Flujo de Contratación

Para grabar el video del capstone, seguí este flujo:

1. `make streamlit-run` — iniciar la web app
2. Crear usuario: nombre + teléfono
3. Chat: "Necesito un plomero en el 06600"
4. Seleccionar proveedor de las cards
5. Confirmar booking (escrow)
6. Mostrar sidebar con reserva activa
7. Check-in / Check-out (simulado)
8. Botón de pánico (opcional)

## 📊 Evaluación

```bash
python tests/eval/generate_traces.py
python tests/eval/evaluate.py
```

## 📹 Demo Video

[Link a tu video de YouTube]
