import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .. import models, crud, agent
from ..database import get_db
from ..auth import get_current_tenant_flexible

router = APIRouter(prefix="/settings", tags=["settings"])


class ApiKeyUpdate(BaseModel):
    openai_api_key: str


@router.get("/api-key")
def get_api_key(tenant: models.Tenant = Depends(get_current_tenant_flexible)):
    groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    key = groq_key or gemini_key or openai_key
    if not key:
        return {"configured": False, "masked_key": "", "provider": "none"}
    if groq_key or key.startswith("gsk_"):
        provider = "Groq Llama-3.3 (100% Free)"
    elif key.startswith("sk-"):
        provider = "OpenAI"
    else:
        provider = "Google Gemini (100% Free)"
    masked = key[:7] + "..." + key[-4:] if len(key) > 11 else "****"
    return {"configured": True, "masked_key": masked, "provider": provider}


@router.post("/api-key")
def update_api_key(payload: ApiKeyUpdate, tenant: models.Tenant = Depends(get_current_tenant_flexible)):
    new_key = payload.openai_api_key.strip()
    if not new_key:
        raise HTTPException(status_code=400, detail="API Key cannot be empty")

    if new_key.startswith("gsk_"):
        provider = "Groq Llama-3.3 (100% Free)"
        os.environ["GROQ_API_KEY"] = new_key
    elif new_key.startswith("sk-"):
        provider = "OpenAI"
        os.environ["OPENAI_API_KEY"] = new_key
    else:
        provider = "Google Gemini (100% Free)"
        os.environ["GEMINI_API_KEY"] = new_key

    # Update .env file on disk
    try:
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        key_name = "GROQ_API_KEY" if new_key.startswith("gsk_") else ("OPENAI_API_KEY" if new_key.startswith("sk-") else "GEMINI_API_KEY")
        updated = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key_name}="):
                new_lines.append(f"{key_name}={new_key}\n")
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f"\n{key_name}={new_key}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception:
        pass

    masked = new_key[:7] + "..." + new_key[-4:] if len(new_key) > 11 else "****"
    return {
        "status": "ok",
        "message": f"{provider} API Key saved and active for real-time replies!",
        "configured": True,
        "masked_key": masked,
        "provider": provider,
    }


class SystemPromptUpdate(BaseModel):
    system_prompt: str


class SystemPromptTestIn(BaseModel):
    system_prompt: str
    message: str


DEFAULT_PROMPT_TEMPLATES = [
    {
        "id": "professional_support",
        "name": "👔 Professional Support",
        "description": "Polite, formal, and authoritative. Ideal for corporate, B2B, and professional services.",
        "prompt": "You are a professional, polite, and helpful AI support representative for {tenant_name}.\n\nRules:\n1. Maintain a professional, empathetic, and respectful tone at all times.\n2. Answer customer queries strictly using the provided knowledge base.\n3. If a question is outside the knowledge base, politely state that our team will follow up shortly.\n4. If the customer wishes to book an appointment, collect their name, contact detail, and preferred time gracefully."
    },
    {
        "id": "friendly_sales",
        "name": "🚀 Friendly Sales & Appointment Setter",
        "description": "Energetic, engaging, and focused on turning conversations into bookings.",
        "prompt": "You are a friendly, enthusiastic, and high-converting sales assistant for {tenant_name}.\n\nRules:\n1. Be warm, welcoming, and use conversational language suitable for chat apps.\n2. Highlight key benefits of our services based on the knowledge base.\n3. Actively encourage customers to book a consultation or appointment when they express interest.\n4. Collect their name, contact details, and preferred appointment time."
    },
    {
        "id": "medical_clinic",
        "name": "🏥 Medical & Clinic Assistant",
        "description": "Warm, empathetic, and disclaimer-ready for healthcare and clinical services.",
        "prompt": "You are a caring and attentive clinic coordinator for {tenant_name}.\n\nRules:\n1. Be compassionate and gentle in your communication.\n2. Answer clinic timings, doctor schedules, and service details strictly from the knowledge base.\n3. For medical emergencies, advise the patient to visit the nearest hospital or emergency room immediately.\n4. Assist patients in booking appointments by collecting name, phone number, and preferred date/time."
    },
    {
        "id": "ecommerce_retail",
        "name": "🛒 E-Commerce & Service Assistant",
        "description": "Concise, direct, and focused on quick answers about products, pricing, and orders.",
        "prompt": "You are a fast, helpful customer service assistant for {tenant_name}.\n\nRules:\n1. Give short, direct, and crystal-clear answers.\n2. Provide accurate pricing, product info, and policy details from the knowledge base.\n3. Offer quick guidance on how to order or get in touch with our team."
    }
]


@router.get("/system-prompt")
def get_system_prompt(
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible)
):
    saved_prompt = crud.get_tenant_system_prompt(db, tenant.id)
    return {
        "system_prompt": saved_prompt,
        "default_templates": DEFAULT_PROMPT_TEMPLATES
    }


@router.post("/system-prompt")
def update_system_prompt(
    payload: SystemPromptUpdate,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible)
):
    updated = crud.update_tenant_system_prompt(db, tenant.id, payload.system_prompt.strip())
    return {
        "status": "ok",
        "message": "Custom System Prompt saved and active for your AI agent!",
        "system_prompt": updated
    }


@router.post("/system-prompt/test")
def test_system_prompt(
    payload: SystemPromptTestIn,
    db: Session = Depends(get_db),
    tenant: models.Tenant = Depends(get_current_tenant_flexible)
):
    kb_entries = crud.get_active_knowledge(db, tenant.id)
    custom_prompt = payload.system_prompt.strip()

    reply_obj = agent.generate_reply_with_custom_prompt(
        tenant_name=tenant.name,
        custom_prompt=custom_prompt,
        kb_entries=kb_entries,
        history=[],
        new_message=payload.message
    )
    return reply_obj
