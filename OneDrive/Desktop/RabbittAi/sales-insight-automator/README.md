# RabbittAi — Sales Insight Automator

Upload sales data (CSV/XLSX), generate an AI-powered executive summary via Google Gemini, and email it to stakeholders — complete with a revenue-by-region chart.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![React](https://img.shields.io/badge/React-19-61DAFB)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

## Features

- **CSV / XLSX Upload** — drag-and-drop or click to upload sales files
- **AI Executive Summary** — Google Gemini generates a professional numbered-point report
- **Revenue Chart** — matplotlib bar chart of revenue by region embedded in the email
- **Email Delivery** — HTML email with inline chart sent via Gmail SMTP
- **Rate Limiting** — 30 requests/minute per IP (slowapi)
- **File Validation** — only `.csv`/`.xlsx`, max 5 MB
- **Dockerized** — one-command deployment with `docker compose`
- **Deploy-ready** — Vercel (frontend) + Render (backend) configs included
- **CI/CD** — GitHub Actions pipeline with lint, type check, build, and integration test

## Architecture

```
┌──────────────┐        ┌──────────────────┐        ┌─────────────┐
│   React UI   │──POST──│  FastAPI Backend  │──API──▶│ Google      │
│  (Vite)      │  :8000 │                  │        │ Gemini AI   │
│  :5173       │◀─JSON──│  • parse file    │        └─────────────┘
└──────────────┘        │  • generate AI   │
                        │  • send email    │──SMTP──▶ Gmail
                        └──────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey))
- Gmail App Password ([create one here](https://myaccount.google.com/apppasswords))

### 1. Clone and configure

```bash
git clone <repo-url>
cd sales-insight-automator
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials
```

### 2. Run with Docker Compose (recommended)

```bash
# 1. Build and start both services (backend + frontend)
docker compose up --build

# 2. (Optional) Run in detached mode
docker compose up --build -d

# 3. Check service health
docker compose ps          # both should show "healthy"
curl http://localhost:8000/health   # {"status":"healthy"}

# 4. Stop the stack
docker compose down        # add -v to remove volumes
```

| Service  | URL                          | Notes                       |
|----------|------------------------------|-----------------------------|
| Frontend | http://localhost:5173        | React SPA served by nginx   |
| Backend  | http://localhost:8000        | FastAPI application         |
| API Docs | http://localhost:8000/docs   | Interactive Swagger UI      |

The `docker-compose.yml` ensures the frontend waits for the backend health check to pass (`depends_on → condition: service_healthy`) before starting.

### 3. Run locally (development)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Endpoint Security

All API endpoints are protected with multiple layers:

| Layer | Mechanism | Details |
|-------|-----------|--------|
| **Rate Limiting** | slowapi (30 req/min per IP) | Prevents abuse; returns `429 Too Many Requests` when exceeded |
| **CORS** | FastAPI `CORSMiddleware` | Only the configured `FRONTEND_URL` origin (and its `localhost`/`127.0.0.1` variant) is allowed |
| **File Validation** | `security.py` | Rejects any file that isn't `.csv`/`.xlsx`; enforces a **5 MB** hard cap via both the `Content-Length` header and a streaming byte count |
| **Input Validation** | Pydantic + `python-multipart` | `recipient_email` is validated as a proper email address; malformed requests return `422` |
| **SMTP Auth** | TLS (STARTTLS, port 587) | Credentials loaded from environment variables — never hard-coded |
| **Docker** | Non-root user (`appuser`) | Backend container drops privileges after build; nginx frontend runs as unprivileged process |
| **HTTP Headers** | nginx `add_header` directives | `X-Frame-Options SAMEORIGIN`, `X-Content-Type-Options nosniff`, `Referrer-Policy strict-origin-when-cross-origin` |

## API Reference

### `POST /analyze-sales`

Upload a sales file and send an AI-generated summary email.

| Parameter         | Type   | Description                          |
|-------------------|--------|--------------------------------------|
| `file`            | File   | `.csv` or `.xlsx` sales data (≤5 MB) |
| `recipient_email` | string | Email address to receive the report  |

**Required CSV/XLSX columns:** `Revenue`, `Product_Category`, `Region`, `Units_Sold`, `Status`

**Example:**
```bash
curl -X POST http://localhost:8000/analyze-sales \
  -F "file=@test_data.csv" \
  -F "recipient_email=user@example.com"
```

**Response:**
```json
{
  "status": "success",
  "message": "Sales summary generated and sent."
}
```

### `GET /health`

Health check endpoint. Returns `{"status": "healthy"}`.

## Environment Variables

All configuration lives in `backend/.env`. Copy the example file first:

```bash
cp backend/.env.example backend/.env
```

`backend/.env.example` ships with every required key:

```dotenv
# Google Gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash

# SMTP email configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=
SMTP_PASSWORD=

# Frontend origin for CORS
FRONTEND_URL=http://localhost:5173
```

| Variable         | Description                     | Default                  |
|------------------|---------------------------------|--------------------------|
| `GEMINI_API_KEY` | Google Gemini API key           | *(required)*             |
| `GEMINI_MODEL`   | Gemini model name               | `gemini-2.5-flash`       |
| `SMTP_SERVER`    | SMTP server hostname            | `smtp.gmail.com`         |
| `SMTP_PORT`      | SMTP port                       | `587`                    |
| `SMTP_EMAIL`     | Sender email address            | *(required)*             |
| `SMTP_PASSWORD`  | Sender email app password       | *(required)*             |
| `FRONTEND_URL`   | Frontend origin (CORS)          | `http://localhost:5173`  |

> **Note:** `.env` is in `.gitignore` — credentials are never committed.

## Project Structure

```
sales-insight-automator/
├── .github/workflows/ci.yml    # GitHub Actions CI pipeline
├── .gitignore
├── docker-compose.yml
├── render.yaml                 # Render Blueprint (backend)
├── README.md
├── LICENSE
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   ├── requirements.txt
│   ├── test_data.csv
│   ├── tests/
│   │   ├── test_file_parser.py
│   │   ├── test_security.py
│   │   └── test_email_format.py
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI app, CORS, rate limiter
│       ├── routes.py           # POST /analyze-sales endpoint
│       ├── schemas.py          # Pydantic models
│       ├── security.py         # File validation (type, size)
│       ├── file_parser.py      # CSV/XLSX → metrics extraction
│       ├── ai_service.py       # Google Gemini integration
│       └── email_service.py    # SMTP email with chart
└── frontend/
    ├── Dockerfile
    ├── .dockerignore
    ├── vercel.json              # Vercel deployment config
    ├── nginx.conf
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── UploadForm.jsx
        ├── api.js
        └── styles.css
```

## CI/CD

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs on push/PR to `main`:

1. **Backend** — install deps → ruff lint → mypy type check → Docker build
2. **Frontend** — install deps → vite build → Docker build
3. **Integration** — docker compose up → health check → frontend verify → tear down

**Required GitHub Secrets:** `GEMINI_API_KEY`, `SMTP_EMAIL`, `SMTP_PASSWORD`

## Deployment (Production)

### Frontend → Vercel

1. Push your repo to GitHub.
2. Go to [vercel.com/new](https://vercel.com/new) and import the repository.
3. Set the **Root Directory** to `frontend`.
4. Add one environment variable:
   | Key | Value |
   |-----|-------|
   | `VITE_API_URL` | `https://<your-render-service>.onrender.com` |
5. Click **Deploy**. Vercel auto-detects Vite, runs `npm run build`, and serves `dist/`.

`frontend/vercel.json` is already included with SPA rewrites so all routes resolve to `index.html`.

### Backend → Render

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New → Blueprint**.
2. Connect your repo. Render reads `render.yaml` and creates the service automatically.
3. Fill in the prompted secrets:
   | Key | Value |
   |-----|-------|
   | `GEMINI_API_KEY` | Your Google Gemini API key |
   | `SMTP_EMAIL` | Your Gmail address |
   | `SMTP_PASSWORD` | Gmail App Password |
   | `FRONTEND_URL` | `https://<your-app>.vercel.app` |
4. Render installs deps, starts `uvicorn` on `$PORT`, and exposes the `/health` check.

> **Tip:** Set `FRONTEND_URL` on Render to the exact Vercel URL (including `https://`) so CORS allows the frontend origin.

#### Manual Render setup (without Blueprint)

1. **New → Web Service** → connect repo → set **Root Directory** = `backend`.
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add the same env vars listed above.

## License

MIT
