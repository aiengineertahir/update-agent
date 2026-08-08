import os
import httpx

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = "https://graph.facebook.com/" + GRAPH_API_VERSION

def is_mock_mode():
    return not bool(os.getenv("META_APP_SECRET", "").strip())


def send_facebook_message(page_access_token: str, recipient_psid: str, body: str) -> dict:
    if is_mock_mode() and (not page_access_token or page_access_token == "mock"):
        print(f"[MOCK] facebook messenger -> would send to {recipient_psid}: {body}")
        return {"mock": True}

    try:
        resp = httpx.post(
            f"{GRAPH_BASE}/me/messages",
            params={"access_token": page_access_token},
            json={
                "recipient": {"id": recipient_psid},
                "message": {"text": body},
                "messaging_type": "RESPONSE",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as err:
        error_detail = ""
        if hasattr(err, "response") and err.response is not None:
            error_detail = err.response.text
        print(f"[Meta API Error] Failed to send Facebook message: {err} | Detail: {error_detail}")
        return {"error": str(err), "detail": error_detail}


def send_instagram_message(ig_business_account_id: str, access_token: str, recipient_igsid: str, body: str) -> dict:
    if is_mock_mode() and (not access_token or access_token == "mock"):
        print(f"[MOCK] instagram -> would send to {recipient_igsid}: {body}")
        return {"mock": True}

    try:
        resp = httpx.post(
            f"{GRAPH_BASE}/{ig_business_account_id}/messages",
            params={"access_token": access_token},
            json={
                "recipient": {"id": recipient_igsid},
                "message": {"text": body},
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as err:
        error_detail = ""
        if hasattr(err, "response") and err.response is not None:
            error_detail = err.response.text
        print(f"[Meta API Error] Failed to send Instagram message: {err} | Detail: {error_detail}")
        return {"error": str(err), "detail": error_detail}
