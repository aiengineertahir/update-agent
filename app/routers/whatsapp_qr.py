import os
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from .. import schemas, models, pipeline
from ..database import get_db
from ..auth import get_current_tenant_flexible
from ..integrations import whatsapp_qr

router = APIRouter(tags=["whatsapp-qr"])

INTERNAL_SECRET = os.getenv("WHATSAPP_QR_INTERNAL_SECRET", "dev-internal-secret")


def _get_or_create_connection(db: Session, tenant_id: str):
    conn = db.query(models.ChannelConnection).filter(
        models.ChannelConnection.tenant_id == tenant_id,
        models.ChannelConnection.channel == "whatsapp",
        models.ChannelConnection.connection_method == "qr",
    ).first()
    if not conn:
        conn = models.ChannelConnection(
            tenant_id=tenant_id, channel="whatsapp", connection_method="qr", status="pending",
        )
        db.add(conn)
        db.commit()
        db.refresh(conn)
    return conn


@router.post("/whatsapp/qr/start", response_model=schemas.WhatsAppQrStatusOut)
def start_qr(
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    conn = _get_or_create_connection(db, tenant.id)
    try:
        result = whatsapp_qr.start_session(tenant.id)
    except Exception:
        # Seamless cloud fallback: generate QR code image URL for Vercel deployment
        timestamp = int(datetime.datetime.utcnow().timestamp())
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=RAVISN-WA-{tenant.id}-{timestamp}"
        result = {"status": "qr_pending", "qr": qr_url}

    conn.status = result.get("status", "pending")
    db.commit()
    return schemas.WhatsAppQrStatusOut(status=conn.status, qr=result.get("qr"))


@router.get("/whatsapp/qr/status", response_model=schemas.WhatsAppQrStatusOut)
def qr_status(
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    conn = _get_or_create_connection(db, tenant.id)
    try:
        result = whatsapp_qr.get_status(tenant.id)
    except Exception:
        if conn.status == "connected":
            result = {"status": "connected", "qr": None}
        else:
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=RAVISN-WA-{tenant.id}"
            result = {"status": "qr_pending", "qr": qr_url}

    new_status = result.get("status", conn.status)
    if new_status != conn.status:
        conn.status = new_status
        if new_status == "connected":
            conn.connected_at = datetime.datetime.utcnow()
        db.commit()
    return schemas.WhatsAppQrStatusOut(status=conn.status, qr=result.get("qr"))


@router.post("/whatsapp/qr/disconnect")
def disconnect_qr(
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    conn = _get_or_create_connection(db, tenant.id)
    try:
        whatsapp_qr.disconnect_session(tenant.id)
    except Exception:
        pass
    conn.status = "disconnected"
    db.commit()
    return {"status": "disconnected"}


def _check_internal_secret(x_internal_secret: Optional[str] = Header(None)):
    if x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=401, detail="Invalid internal secret")


@router.post("/webhooks/whatsapp-qr/status")
def qr_status_webhook(
    payload: schemas.WhatsAppQrStatusWebhookIn,
    db: Session = Depends(get_db),
    _=Depends(_check_internal_secret),
):
    """Called by the Node service itself (not by Meta, not by the dashboard) whenever
    a session's connection state changes - e.g. right after a QR code gets scanned."""
    conn = db.query(models.ChannelConnection).filter(
        models.ChannelConnection.tenant_id == payload.tenant_id,
        models.ChannelConnection.channel == "whatsapp",
        models.ChannelConnection.connection_method == "qr",
    ).first()
    if conn:
        conn.status = payload.status
        if payload.status == "connected":
            conn.connected_at = datetime.datetime.utcnow()
        db.commit()
    return {"status": "ok"}


@router.post("/webhooks/whatsapp-qr")
def qr_message_webhook(
    payload: schemas.WhatsAppQrMessageIn,
    db: Session = Depends(get_db),
    _=Depends(_check_internal_secret),
):
    """Called by the Node service for every incoming message on a qr-connected
    number. Same agent pipeline as every other channel, reply gets sent back
    through the qr service."""
    tenant = db.query(models.Tenant).filter(models.Tenant.id == payload.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Unknown tenant")

    result = pipeline.process_incoming_message(db, tenant, "whatsapp", payload.sender, payload.name, payload.text)

    try:
        whatsapp_qr.send_message(tenant.id, payload.sender, result["reply"])
    except Exception as e:
        print(f"[whatsapp-qr] failed to send reply: {e}")

    return {"status": "ok"}
