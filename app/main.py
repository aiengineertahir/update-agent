from dotenv import load_dotenv
load_dotenv()  # must run before any app module reads os.getenv() at import time

import os
from fastapi import FastAPI, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import Base, engine, DATABASE_URL, get_db
from .routers import tenants, knowledge, chat, auth, conversations, whatsapp_official, whatsapp_qr, meta_messaging, bookings, settings, channels, public_legal

# Sqlite (local dev): auto-create tables, zero setup needed.
# Anything else (postgres/production): schema is managed by alembic instead -
# run `alembic upgrade head` before starting the app. Mixing the two would let
# create_all silently paper over a migration you forgot to run.
if DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="RAVISN multi-channel agent")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
origins = ["*"] if CORS_ORIGINS == "*" else [o.strip() for o in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://localhost:8000"] if origins == ["*"] else origins,
    allow_origin_regex=r".*" if origins == ["*"] else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

all_routers = [
    auth.router, tenants.router, knowledge.router, chat.router,
    conversations.router, whatsapp_official.router, whatsapp_qr.router,
    meta_messaging.router, bookings.router, settings.router,
    channels.router, public_legal.router
]

for router in all_routers:
    app.include_router(router)

# Mount all routers under /api prefix for Vercel / serverless routing
api_router = APIRouter(prefix="/api")
for router in all_routers:
    api_router.include_router(router)


@api_router.get("/")
def api_root():
    return {"status": "ok", "service": "ravisn-agent"}


@api_router.get("/health")
def api_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}


app.include_router(api_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "ravisn-agent"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": db_ok}
