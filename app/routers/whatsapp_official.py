import os
import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from .. import schemas, models, pipeline, crud
from ..database import get_db
from ..auth import get_current_tenant_flexible
from ..integrations import whatsapp_official
from ..security import verify_meta_signature

router = APIRouter(tags=["whatsapp-official"])

WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ravisn-dev-verify-token")
APP_SECRET = os.getenv("META_APP_SECRET", "")
MOCK_MODE = not bool(APP_SECRET)


@router.post("/whatsapp/official/connect", response_model=schemas.ChannelConnectionOut)
def connect_official(
    payload: schemas.WhatsAppOfficialConnectIn,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible),
):
    """Manual connect for now (paste phone_number_id + access_token from the Meta
    app dashboard). The one-click embedded signup button needs RAVISN's Meta Tech
    Provider approval + a real app id before it can replace this."""
    extra = {"waba_id": payload.waba_id} if payload.waba_id else None
    return crud.upsert_channel_connection(
        db, tenant.id, "whatsapp", "official_api", payload.phone_number_id, payload.access_token, extra
    )


@router.get("/webhooks/whatsapp")
def verify_webhook(request: Request):
    """Meta calls this once, when the webhook url is first configured, to confirm
    we control this endpoint."""
    verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ravisn-dev-verify-token")
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == verify_token:
        return PlainTextResponse(params.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/whatsapp")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """Meta calls this for every incoming message / status update. We look up which
    tenant owns the receiving phone number, run the message through the same agent
    pipeline as the test endpoint, then send the reply back out over whatsapp."""
    raw_body = await request.body()
    app_secret = os.getenv("META_APP_SECRET", "").strip()

    if app_secret:
        signature = request.headers.get("x-hub-signature-256", "")
        if not verify_meta_signature(raw_body, signature, app_secret):
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(raw_body or b"{}")

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages")
            if not messages:
                continue  # e.g. a delivery/read status update, not a new message

            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            connection = db.query(models.ChannelConnection).filter(
                models.ChannelConnection.channel == "whatsapp",
                models.ChannelConnection.connection_method == "official_api",
                models.ChannelConnection.external_account_id == phone_number_id,
            ).first()
            if not connection:
                continue  # message for a number we don't have on file, ignore

            contacts = {c["wa_id"]: c.get("profile", {}).get("name") for c in value.get("contacts", [])}

            for msg in messages:
                if msg.get("type") != "text":
                    continue  # phase 3 handles text only; media/buttons come later
                sender = msg["from"]
                text = msg.get("text", {}).get("body", "")
                contact_name = contacts.get(sender)

                result = pipeline.process_incoming_message(
                    db, connection.tenant, "whatsapp", sender, contact_name, text
                )
                whatsapp_official.send_message(
                    connection.external_account_id, connection.access_token, sender, result["reply"]
                )

    return {"status": "ok"}
