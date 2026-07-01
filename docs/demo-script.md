# HogarConfianza — Unified Demo Script

**Duration:** ~5 min | **Language:** English | **Audience:** Course instructors + general viewers

---

## 1. The Story + Intro (0:00 – 0:45)

**Visual:** Title card — "HogarConfianza: Multi-Agent Concierge for Trusted Home Services" → slowly fade to speaker

**VO:**
> The idea for this project came from a personal experience. A painter showed up at my door offering his services, telling me a heartbreaking story about his sick son. I felt for him and let him in. At some point we got distracted, and he stole a cellphone and a laptop.
>
> Nothing violent — but the violation of trust was real. And finding reliable service providers? It's a trust lottery. You ask neighbors, search Facebook groups — and you still have no idea who you're letting into your home.
>
> That's why I built HogarConfianza — a multi-agent system that connects Mexican households with verified, trustworthy service providers. Powered by Google ADK.

---

## 2. Architecture (0:45 – 1:15)

**Visual:** Architecture diagram — RootAgent → 4 sub-agents, tools, MCP servers, security callback

**VO:**
> A RootAgent orchestrates four specialized sub-agents. Every message passes through a SecurityScreen — a `before_model_callback` — that redacts PII and detects prompt injection before the LLM ever sees it.
>
> **TriageAgent** classifies the service. **MatchingAgent** searches providers with Maps-powered distance ranking. **SafetyAgent** handles check-in/out and panic alerts. **BookingAgent** manages escrow payments with human-in-the-loop approval.
>
> Two MCP servers provide the service catalog and Google Maps capabilities. 17 ADK tools across all agents.

---

## 3. Live Demo (1:15 – 3:45)

### 3a — Triage + Matching (1:15 – 1:50)

**Visual:** Streamlit UI → language toggle EN → register name/phone → type: "I need a plumber urgently, I have a water leak in Roma, CDMX"

**VO:**
> Let me switch to English and register quickly — just name and phone. Now: "I need a plumber urgently, I have a water leak in Roma."
>
> The TriageAgent classifies this as plumbing and transfers to MatchingAgent, which asks for a full address to calculate proximity.

### 3b — Geocoding + Provider Cards (1:50 – 2:25)

**Visual:** User types address → provider cards appear with ratings, trust scores, badges, distance

**VO:**
> The address triggers `geocode_address` — our Google Maps tool — converting it to GPS coordinates. Then `calculate_distance` ranks providers by proximity.
>
> Providers are returned as visual cards with trust scores, verification status, insurance badges, and distance. Each shows real data. Notice this provider has a low trust score and no insurance — the agent explicitly warns "not verified, use at your own risk." Safety-first design.

### 3c — Escrow + HITL (2:25 – 3:00)

**Visual:** Select Maria Garcia → create_escrow_booking → "Do you APPROVE the $3,200 MXN deposit?"

**VO:**
> I'll select Maria Garcia — trust score 4.9, verified, insured. The BookingAgent calls `create_escrow_booking`: the payment is held in guarantee, not released to the provider until service is complete.
>
> Now the critical moment: the agent asks me to APPROVE or REJECT. It cannot auto-approve any service over $100. I must confirm explicitly. That's human-in-the-loop applied to financial transactions.

### 3d — Check-in / Check-out + Safety (3:00 – 3:45)

**Visual:** Sidebar → booking status → click check-in → check-out → hover panic button

**VO:**
> When the booking is confirmed, the sidebar shows check-in and check-out buttons. The provider checks in on arrival — our system logs location and notifies a trusted contact. On departure, they check out with hours logged.
>
> And if anything feels wrong — the red panic button triggers an emergency protocol: trusted contact notified, provider blocked, security team alerted.

---

## 4. Security (3:45 – 4:05)

**Visual:** Code snippet of `pii_redactor.py` — regex patterns + injection detection

**VO:**
> Behind the scenes, the SecurityScreen redacts six types of PII — phone numbers, emails, credit cards, CURP, addresses — using regex patterns. It also detects prompt injection across 8 patterns in both Spanish and English.
>
> If injection is detected, the callback returns a blocked response immediately — the LLM never processes the malicious input.

---

## 5. Testing & Deployment (4:05 – 4:40)

**Visual:** Terminal → `make test` → 69 passing → `make docker-build` → `make deploy` → Cloud Run

**VO:**
> 69 automated tests cover database models, all agent tools, the Maps client, and the complete escrow lifecycle — including edge cases like dual-confirmation payment release.
>
> The app is containerized with a multi-stage Docker build and deploys to Cloud Run in two commands. For production, it connects to Cloud SQL PostgreSQL.

---

## 6. Outro (4:40 – 5:00)

**Visual:** Final screen — repo link + thank you

**VO:**
> HogarConfianza demonstrates multi-agent orchestration, ADK tools, MCP integration, security callbacks, human-in-the-loop, and cloud deployment — all applied to a real problem that affects millions of households.
>
> Full source code is on GitHub. Thank you for watching.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Run demo (web) | `make web` |
| Run demo (Streamlit) | `make streamlit-run` |
| Run tests | `make test` |
| Docker build | `make docker-build` |
| Deploy to Cloud Run | `make deploy` |

## Key Providers for Demo

| Name | Service | Trust | Verified | Insurance | Why |
|------|---------|-------|----------|-----------|-----|
| Maria Garcia | Electrical | 4.9 | ✅ | ✅ | Best pick — safe choice |
| Juan Perez | Plumbing | 4.7 | ✅ | ✅ | Solid second option |
| Pedro Hernandez | Gardening | 3.2 | ❌ | ❌ | Use to demo safety warning |

## Fastest Demo Path

1. Open Streamlit: `make streamlit-run`
2. Toggle EN, register name + phone
3. Chat: "I need a plumber urgently, I have a water leak in Roma, CDMX"
4. Address: "Calle Salamanca 154, Colonia Roma, CDMX"
5. Select Maria Garcia → approve booking → check-in → check-out
