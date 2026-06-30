# HogarConfianza — Demo Video Script

**Duration:** ~5 min | **Language:** English | **Audience:** Course creators / instructors

---

## 1. Introduction (0:00 – 0:20)

**Visual:** Title card — "HogarConfianza: Multi-Agent Concierge for Trusted Home Services"

**VO:**
> This is HogarConfianza — a multi-agent system that connects Mexican households with verified, trustworthy service providers. Built with Google ADK for the 5-Day AI Agents Intensive Course.
>
> Let me show you what I built and how each concept from the course comes together.

---

## 2. Architecture (0:20 – 0:50)

**Visual:** Architecture diagram — RootAgent → 4 sub-agents, tools, MCP servers, security

**VO:**
> A RootAgent orchestrates four specialized sub-agents. Every user message first passes through a SecurityScreen — built as a `before_model_callback` — that redacts PII and detects prompt injection before the LLM ever sees it.
>
> - **TriageAgent** classifies the service type
> - **MatchingAgent** searches providers with Maps-powered distance ranking
> - **SafetyAgent** handles check-in/out, panic button, incident reporting
> - **BookingAgent** manages escrow with human-in-the-loop approval
>
> Each agent has its own set of ADK tools. Two MCP servers provide the service catalog and Google Maps capabilities.

---

## 3. Live Demo — ADK Web Playground (0:50 – 3:30)

### 3a — Triage + Matching (0:50 – 1:30)

**Visual:** Terminal → `make web` → browser opens → type: "I need a plumber in Roma, CP 06600"

**VO:**
> Starting the ADK web playground with a single command. The user says: "I need a plumber in Roma, zip code 06600."
>
> The TriageAgent correctly classifies this as plumbing and transfers to MatchingAgent. The agent asks for a full address — this triggers our Maps integration.

### 3b — Address Geocoding + Distance (1:30 – 1:55)

**Visual:** User gives address → agent calls `geocode_address` → coordinates appear → `calculate_distance` runs

**VO:**
> The user provides their address. The agent calls `geocode_address` — our custom ADK tool wrapping the Google Maps API — converting it to GPS coordinates. Then `calculate_distance` ranks providers by proximity.
>
> This is the Maps tool integration, combining trust scores with real distance data.

### 3c — Provider Selection (1:55 – 2:20)

**Visual:** Provider list with ratings, trust scores, badges

**VO:**
> Providers are returned sorted by trust score AND proximity — a weighted ranking. Each shows verification status, insurance, and trust score. One provider has a trust score of 3.2 with no insurance — the agent explicitly warns: "not verified, use at your own risk." This is our safety-first design.

### 3d — Escrow + HITL (2:20 – 2:55)

**Visual:** User selects Maria Garcia → create_escrow_booking → "Do you approve $3,200 MXN deposit?"

**VO:**
> The user selects Maria Garcia — trust score 4.9, verified, insured. The BookingAgent calls `create_escrow_booking`: the payment is held in guarantee, not released to the provider.
>
> Then the critical HITL moment: the agent asks "Do you APPROVE or REJECT this booking?" It cannot auto-approve any service over $100. The user must explicitly confirm. This is the human-in-the-loop pattern from the course, applied to financial transactions.

### 3e — Safety Check-in/out (2:55 – 3:30)

**Visual:** Streamlit sidebar → show booking → click check-in → check-out → panic button

**VO:**
> Switching to our Streamlit UI for the safety flow. When a booking is confirmed, the sidebar shows check-in and check-out buttons. Clicking check-in simulates provider arrival with selfie confirmation and GPS verification — the SafetyAgent logs everything.
>
> And the red panic button triggers the emergency protocol: trusted contact is notified, provider is blocked, security team is alerted. This is the safety agent in action.

---

## 4. Security (3:30 – 3:55)

**Visual:** Show `pii_redactor.py` — patterns + injection detection

**VO:**
> The SecurityScreen, running as a `before_model_callback`, redacts six types of PII — phone numbers, emails, credit cards, CURP, addresses — using regex patterns. It also detects prompt injection across 8 patterns in both Spanish and English.
>
> If injection is detected, the callback returns a blocked response immediately — the LLM never processes the malicious input.

---

## 5. Testing & Evaluation (3:55 – 4:20)

**Visual:** Terminal → tests pass → eval results

**VO:**
> 63 automated tests cover the database models, all agent tools, the Maps client, and the complete escrow lifecycle — including edge cases like dual-confirmation payment release.
>
> Beyond unit tests, an evaluation framework runs 8 real-world scenarios through LLM-as-judge, scoring on routing correctness, security containment, and safety protocol adherence.

---

## 6. Deployment to Google Cloud (4:20 – 4:45)

**Visual:** Terminal → `make docker-build` → `make deploy` → Cloud Run dashboard

**VO:**
> The app is containerized with a multi-stage Docker build and deploys to Cloud Run in two commands: `make docker-build` pushes to Artifact Registry, `make deploy` creates a serverless, auto-scaling service with TLS and health checks.
>
> For production, it connects to Cloud SQL PostgreSQL. Without a database URL, it uses local SQLite — perfect for development.

---

## 7. Outro (4:45 – 5:00)

**Visual:** Final screen — repo link

**VO:**
> HogarConfianza demonstrates multi-agent orchestration, ADK tools, MCP integration, security callbacks, human-in-the-loop, and cloud deployment — all concepts from this course applied to a real-world problem.
>
> Thank you for this incredible course. Full source code is on GitHub.

---

## Quick Reference

| Action | Command |
|--------|---------|
| ADK Web (Antigravity) | `make web` |
| Run tests | `make test` |
| Run evaluation | `python tests/eval/generate_traces.py && python tests/eval/evaluate.py` |
| Docker build | `make docker-build` |
| Deploy to Cloud Run | `make deploy` |
| Streamlit UI | `make streamlit-run` |

## Key Providers for Demo

| Provider | Service | Trust | Verified | Insurance |
|----------|---------|-------|----------|-----------|
| Maria Garcia | Electricidad | 4.9 | ✅ | ✅ |
| Juan Perez | Plomeria | 4.7 | ✅ | ✅ |
| Pedro Hernandez | Jardineria | 3.2 | ❌ | ❌ |

**Demo zip codes:** `06600` (Roma), `06700` (Del Valle)

## Fastest Demo Path

1. `make web` → chat "I need a plumber in Roma, CP 06600"
2. Address → "Calle Salamanca 154, Colonia Roma, CDMX"
3. "I want to hire Juan Perez" → "Yes, I approve" (HITL)
4. `make streamlit-run` → sidebar shows booking → check-in → check-out
