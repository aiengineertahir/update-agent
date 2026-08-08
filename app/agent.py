import os
import json
from typing import List
from . import models

MOCK_MODE = not bool(os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT_TEMPLATE = """You are the WhatsApp/Instagram/Facebook assistant for {tenant_name}.

Rules:
1. Answer ONLY using the knowledge base below. Never use outside knowledge, never guess, never make anything up.
2. If the customer's question is not covered by the knowledge base, do not attempt to answer it. Say a team member will follow up shortly instead.
3. If the customer wants to book an appointment or meeting, collect their name, a contact detail, and a preferred time through natural back-and-forth conversation. Do not invent booking details the customer has not given you.
4. Keep replies short and conversational, suitable for a chat app.

Knowledge base:
{kb_text}

Respond with ONLY a JSON object, no other text, in exactly this shape:
{{"reply": "<message to send back>", "booking_ready": <true or false>, "booking_info": {{"name": "<or null>", "contact": "<or null>", "preferred_time": "<or null>", "notes": "<or null>"}}}}

Set booking_ready to true only once you have at least a name and a contact detail or preferred time.
"""


def build_kb_text(kb_entries: List[models.KnowledgeEntry]) -> str:
    if not kb_entries:
        return "(no knowledge base entries yet)"
    lines = []
    for e in kb_entries:
        lines.append("Q: " + e.question + "\nA: " + e.answer)
    return "\n\n".join(lines)


def build_messages(system_prompt: str, history: List[models.Message], new_message: str):
    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        role = "user" if m.direction == "inbound" else "assistant"
        messages.append({"role": role, "content": m.body})
    messages.append({"role": "user", "content": new_message})
    return messages


def is_mock_mode():
    gemini_key = os.getenv("GEMINI_API_KEY") or ""
    openai_key = os.getenv("OPENAI_API_KEY") or ""
    key = gemini_key.strip() or openai_key.strip()
    return not bool(key)


def call_gemini(api_key: str, messages: list):
    system_instruction = ""
    prompt_parts = []
    for m in messages:
        if m["role"] == "system":
            system_instruction = m["content"]
        elif m["role"] == "user":
            prompt_parts.append(f"Customer: {m['content']}")
        elif m["role"] == "assistant":
            prompt_parts.append(f"Assistant: {m['content']}")

    full_prompt = (
        system_instruction
        + "\n\nConversation history:\n"
        + "\n".join(prompt_parts)
        + "\n\nRespond with ONLY the JSON object as requested above:"
    )

    models_to_try = [
        os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "gemini-2.0-flash-lite",
    ]

    last_err = None
    for model_name in models_to_try:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            return response.text
        except Exception as e:
            last_err = e
            try:
                import httpx

                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "response_mime_type": "application/json",
                        "temperature": 0.3,
                    },
                }
                res = httpx.post(url, json=payload, timeout=30.0)
                res_json = res.json()
                if "error" in res_json:
                    raise Exception(res_json["error"].get("message", "Gemini API error"))
                return res_json["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e2:
                last_err = e2
                continue

    raise last_err


def call_llm(messages):
    if is_mock_mode():
        last_user = messages[-1]["content"]
        lower = last_user.lower()
        wants_booking = ("book" in lower) or ("appointment" in lower)
        mock_reply = "[MOCK MODE - add GEMINI_API_KEY in Settings/env for real replies] Aap ne likha: " + last_user
        return json.dumps({
            "reply": mock_reply,
            "booking_ready": wants_booking,
            "booking_info": {
                "name": "Test User",
                "contact": "923000000000",
                "preferred_time": "tomorrow",
                "notes": "captured in mock mode",
            } if wants_booking else None,
        })

    api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()

    if not api_key.startswith("sk-"):
        try:
            return call_gemini(api_key, messages)
        except Exception as err:
            err_msg = str(err)
            if "429" in err_msg or "quota" in err_msg.lower():
                reply_text = "[Gemini AI Error: You exceeded your API key quota (429 Rate Limit). Please get a fresh free API key from https://aistudio.google.com/app/apikey and save it in Settings.]"
            else:
                reply_text = f"[Gemini AI Error: {err_msg}]"
            return json.dumps({
                "reply": reply_text,
                "booking_ready": False,
                "booking_info": None,
            })
    else:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as err:
            err_msg = str(err)
            return json.dumps({
                "reply": f"[OpenAI Error: {err_msg}]",
                "booking_ready": False,
                "booking_info": None,
            })


def find_kb_match(kb_entries, new_message: str):
    if not kb_entries:
        return None
    msg_clean = new_message.strip().lower()
    if not msg_clean:
        return None

    # 1. Exact match
    for e in kb_entries:
        if e.question.strip().lower() == msg_clean:
            return e.answer

    # 2. Substring match
    for e in kb_entries:
        q_clean = e.question.strip().lower()
        if q_clean and (q_clean in msg_clean or msg_clean in q_clean):
            return e.answer

    # 3. Word match
    msg_words = set(w for w in msg_clean.split() if len(w) > 2)
    if msg_words:
        for e in kb_entries:
            q_words = set(w for w in e.question.strip().lower().split() if len(w) > 2)
            if msg_words.intersection(q_words):
                return e.answer

    return None


def generate_reply(tenant_name: str, kb_entries, history, new_message: str):
    # Check Knowledge Base directly first for instant accurate response
    kb_direct_answer = find_kb_match(kb_entries, new_message)

    kb_text = build_kb_text(kb_entries)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(tenant_name=tenant_name, kb_text=kb_text)
    messages = build_messages(system_prompt, history, new_message)
    raw = call_llm(messages)
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        parsed = {
            "reply": raw if isinstance(raw, str) else "Sorry, kuch masla hua, thori dair mein try karein.",
            "booking_ready": False,
            "booking_info": None,
        }
    parsed.setdefault("reply", "")
    parsed.setdefault("booking_ready", False)
    parsed.setdefault("booking_info", None)

    # If AI returned an error message or mock notice, override with KB answer if available
    reply_str = parsed.get("reply", "")
    if reply_str.startswith("[") or "Error" in reply_str or "MOCK MODE" in reply_str or not reply_str:
        if kb_direct_answer:
            parsed["reply"] = kb_direct_answer
        elif not reply_str or reply_str.startswith("["):
            parsed["reply"] = "Aap ka shukriya! Hamari team jald aap se rabta karegi."

    return parsed
