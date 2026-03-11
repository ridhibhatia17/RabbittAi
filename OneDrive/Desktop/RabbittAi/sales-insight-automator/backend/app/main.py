"""Sales Insight Automator — FastAPI application entry point."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.routes import router

# Load .env from the backend directory (parent of app/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Sales Insight Automator",
    description=(
        "Upload sales data (CSV / XLSX), generate an AI-powered executive "
        "summary via Google Gemini, and email it to stakeholders."
    ),
    version="1.0.0",
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — allow the configured frontend origin (localhost & 127.0.0.1)
# ---------------------------------------------------------------------------
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
allowed_origins = [o.strip() for o in frontend_url.split(",") if o.strip()]

# For each origin, also allow localhost ↔ 127.0.0.1 swaps
extra = []
for origin in allowed_origins:
    if "localhost" in origin:
        extra.append(origin.replace("localhost", "127.0.0.1"))
    elif "127.0.0.1" in origin:
        extra.append(origin.replace("127.0.0.1", "localhost"))
allowed_origins.extend(extra)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
