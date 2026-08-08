import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .. import models
from ..auth import get_current_tenant_flexible

router = APIRouter(prefix="/settings", tags=["settings"])


class ApiKeyUpdate(BaseModel):
    openai_api_key: str


@router.get("/api-key")
def get_api_key(tenant: models.Tenant = Depends(get_current_tenant_flexible)):
    key = (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        return {"configured": False, "masked_key": "", "provider": "none"}
    provider = "OpenAI" if key.startswith("sk-") else "Google Gemini (Free)"
    masked = key[:7] + "..." + key[-4:] if len(key) > 11 else "****"
    return {"configured": True, "masked_key": masked, "provider": provider}


@router.post("/api-key")
def update_api_key(payload: ApiKeyUpdate, tenant: models.Tenant = Depends(get_current_tenant_flexible)):
    new_key = payload.openai_api_key.strip()
    if not new_key:
        raise HTTPException(status_code=400, detail="API Key cannot be empty")

    provider = "OpenAI" if new_key.startswith("sk-") else "Google Gemini (Free)"

    # 1. Update in-memory env
    os.environ["GEMINI_API_KEY"] = new_key
    os.environ["OPENAI_API_KEY"] = new_key

    # 2. Try updating .env file on disk if writable (local dev)
    try:
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
        lines = []
        gemini_updated = False
        openai_updated = False
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                if line.strip().startswith("GEMINI_API_KEY="):
                    new_lines.append(f"GEMINI_API_KEY={new_key}\n")
                    gemini_updated = True
                elif line.strip().startswith("OPENAI_API_KEY="):
                    new_lines.append(f"OPENAI_API_KEY={new_key}\n")
                    openai_updated = True
                else:
                    new_lines.append(line)
            lines = new_lines

        if not gemini_updated:
            lines.append(f"\nGEMINI_API_KEY={new_key}\n")
        if not openai_updated:
            lines.append(f"OPENAI_API_KEY={new_key}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception:
        # File is read-only on Vercel/serverless environments.
        pass

    masked = new_key[:7] + "..." + new_key[-4:] if len(new_key) > 11 else "****"
    return {
        "status": "ok",
        "message": f"{provider} API Key saved and active for real-time replies!",
        "configured": True,
        "masked_key": masked,
        "provider": provider,
    }
