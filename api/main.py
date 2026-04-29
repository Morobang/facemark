"""
api/main.py
-----------
FastAPI server that exposes the face engine via HTTP.
Your Next.js website calls these endpoints.

Run with:
    python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
from config.settings import ALLOWED_ORIGINS, ORG_NAME
from engine.face_engine import FaceEngine

# ── Shared engine instance ────────────────────────────────────────────────────
engine: FaceEngine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    logger.info("Starting Facemark API...")
    engine = FaceEngine()
    yield
    logger.info("Shutting down...")
    engine.close()

app = FastAPI(
    title=f"{ORG_NAME} — Facemark API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"service": "Facemark API", "org": ORG_NAME, "status": "running"}

# Import routes after app is created
from api.routes import members, attendance
app.include_router(members.router)
app.include_router(attendance.router)