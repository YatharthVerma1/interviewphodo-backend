# InterviewPhodo Backend

Real-time AI mock interview API for Indian BTech students.

## Stack

- **FastAPI** — REST + WebSocket API
- **Supabase** — Postgres + Auth (JWT validation)
- **Daily.co** — WebRTC video/audio rooms
- **Pipecat** — real-time audio pipeline
- **Gemini Live API** — voice AI interviewer

## Setup

### 1. Create a virtual environment

**Use Python 3.11 or 3.12** (Pipecat does not support Python 3.14 yet).

```bash
cd interviewphodo-backend
python3.12 -m venv .venv   # or python3.11
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-pipecat.txt
```

For API-only development without the live interview pipeline:

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in at minimum (core path):

| Variable | Where to get it |
|----------|-----------------|
| `SUPABASE_URL` | Supabase → Project Settings → API |
| `SUPABASE_SERVICE_KEY` | Same page (service_role — backend only) |
| `DAILY_API_KEY` | daily.co → Developers |
| `GOOGLE_API_KEY` | aistudio.google.com |

Optional (deferred):

- `R2_*` — resume PDF upload
- `RAZORPAY_*` — payment packs

### 3. Apply database schema

Open Supabase **SQL Editor** and run:

```
supabase/migrations/001_initial_schema.sql
```

This creates `users`, `sessions`, `reports`, `payment_orders` plus RLS policies and an auth signup trigger.

### 4. Run the server

```bash
uvicorn main:app --reload
```

Health check: http://localhost:8000/health

API docs: http://localhost:8000/docs

## Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service status |
| GET | `/api/auth/me` | Current user profile (JWT required) |
| POST | `/api/sessions/start` | Start interview, get Daily room URL |
| GET | `/api/sessions/{id}/status` | Live FSM phase + turn count |
| WS | `/ws/avatar/{session_id}?token=<jwt>` | Avatar event stream |

## Verify without frontend

1. Create a test user in Supabase Dashboard → Authentication
2. Copy their access token from the auth session
3. Test profile:

```bash
curl -H "Authorization: Bearer YOUR_JWT" http://localhost:8000/api/auth/me
```

4. Start a session:

```bash
curl -X POST http://localhost:8000/api/sessions/start \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"company":"tcs","round_type":"hr"}'
```

## Project layout

```
interviewphodo-backend/
├── main.py                 # FastAPI app entry point
├── config.py               # Environment settings
├── routers/                # HTTP + WebSocket routes
├── services/               # Daily, Pipecat pipeline, FSM, reports
├── prompts/                # Company configs + prompt builder
├── models/                 # Pydantic request/response schemas
├── database/               # Supabase client
└── supabase/migrations/    # SQL schema
```
