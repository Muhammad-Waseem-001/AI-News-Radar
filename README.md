# AI News Intelligence & Sentiment Radar

Production-ready starter that:

- Scrapes AI news via RSS
- Summarizes/classifies/scores sentiment with Google Gemini
- Sends Gmail alerts + daily digest
- Displays insights in a React dashboard
- Persists data in Supabase Postgres
- Runs automated jobs on Vercel Cron (serverless-safe)

## Architecture

- `frontend/`: React + Vite dashboard
- `backend/`: FastAPI API + Gemini enrichment + Gmail integration
- DB: Supabase Postgres (`DATABASE_URL`)
- Scheduler:
  - Vercel Cron in production (`/api/v1/cron/*`)
  - Optional local APScheduler (`ENABLE_LOCAL_SCHEDULER=true`)

## Key Backend Endpoints

- `GET /health`
- `GET /api/v1/stats`
- `GET /api/v1/articles`
- `GET /api/v1/articles/{id}`
- `POST /api/v1/jobs/ingest` (manual)
- `POST /api/v1/jobs/digest` (manual)
- `GET /api/v1/cron/ingest` (Vercel cron)
- `GET /api/v1/cron/digest` (Vercel cron, de-duplicated once/day by local date)

## Local Setup

## 1) Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set real values in `backend/.env`:

- `DATABASE_URL` (Supabase Postgres)
- `GEMINI_API_KEY`
- `GMAIL_USERNAME`
- `GMAIL_APP_PASSWORD`
- `ALERT_RECIPIENTS`
- `DIGEST_RECIPIENTS`

Run backend:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 2) Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open:

- Backend docs: `http://127.0.0.1:8000/docs`
- Frontend: `http://127.0.0.1:5173`

## Supabase Setup

1. Create a Supabase project.
2. Get Postgres connection string from Supabase (`Connect` -> `Transaction pooler` recommended).
3. Set `DATABASE_URL` in `backend/.env` using SQLAlchemy psycopg format, for example:
   - `postgresql+psycopg://postgres.<project_ref>:[PASSWORD]@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require`
4. Keep `AUTO_CREATE_TABLES=true` for first boot to auto-create tables.

## Deploy To Vercel (Recommended: 2 Projects)

Use two Vercel projects from same repo:

1. Backend project with Root Directory = `backend`
2. Frontend project with Root Directory = `frontend`

### Backend on Vercel

Files already added:

- `backend/api/index.py` (Vercel entrypoint)
- `backend/vercel.json` (functions + cron + rewrites)

Default cron schedules in `backend/vercel.json`:

- Ingest: `0 12 * * *` (12:00 UTC)
- Digest: `0 13 * * *` (13:00 UTC)

Set backend env vars in Vercel:

- `DATABASE_URL`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GMAIL_USERNAME`
- `GMAIL_APP_PASSWORD`
- `ALERT_RECIPIENTS`
- `DIGEST_RECIPIENTS`
- `ALERT_SENTIMENT_THRESHOLD`
- `RSS_FEEDS`
- `MAX_ARTICLES_PER_FEED`
- `TIMEZONE`
- `AUTO_CREATE_TABLES=true`
- `ENABLE_LOCAL_SCHEDULER=false`
- `CRON_SECRET=<long-random-secret>`
- `CORS_ORIGINS=https://<your-frontend>.vercel.app`

Important:

- Vercel cron sends `Authorization: Bearer <CRON_SECRET>` when `CRON_SECRET` is set.
- Cron frequency depends on your Vercel plan. Update `backend/vercel.json` schedules as needed.

### Frontend on Vercel

Set frontend env var:

- `VITE_API_BASE_URL=https://<your-backend>.vercel.app/api/v1`

Then redeploy frontend.

## Email Automation Behavior

With backend deployed and cron active:

- Cron ingestion endpoint fetches + enriches + stores articles.
- Negative items trigger alert emails immediately.
- Digest cron endpoint sends at most one digest per local day (dedupe table `job_runs`).

## Security Notes

- Never commit real `.env` values.
- Rotate any API keys/passwords accidentally exposed.
- Keep `CRON_SECRET` set in production.
