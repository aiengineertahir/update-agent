from dotenv import load_dotenv
load_dotenv()  # must run before any app module reads os.getenv() at import time

import os
from fastapi import FastAPI, Depends
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
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(knowledge.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(whatsapp_official.router)
app.include_router(whatsapp_qr.router)
app.include_router(meta_messaging.router)
app.include_router(bookings.router)
app.include_router(settings.router)
app.include_router(channels.router)
app.include_router(public_legal.router)


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
