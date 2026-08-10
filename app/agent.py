import os
import json
from typing import List
from . import models

MOCK_MODE = not bool(os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT_TEMPLATE = """You are an intelligent, friendly AI Conversational Representative for {tenant_name}.

REAL-TIME INTENT RECOGNITION & CROSS-KNOWLEDGE EXTRACTION RULES:
1. INTENT RECOGNITION: Carefully analyze the customer's message to understand their underlying INTENT (e.g. pricing, packages, location, services offered, appointments, business hours, contact details, process, timeline).
2. CROSS-KNOWLEDGE EXTRACTION: If an exact matching question title is not found, SEARCH across all provided Knowledge Base entries below. EXTRACT any relevant facts, lists, bullet points, prices, or details from ANY part of the Knowledge Base that relates to the customer's intent, and synthesize a clear, helpful reply!
3. NATURAL REAL-TIME CHAT: Talk like a helpful, smart human customer assistant in real-time chat! Keep replies concise (1-3 conversational sentences), warm, and engaging. Never dump raw unformatted documents.
4. DYNAMIC LANGUAGE MATCHING: Always respond in the EXACT same language and script used by the customer in their message!
   - If Roman Urdu (e.g. "kitne paise hain?", "apka office kidhar hai?", "kab tak ready hoga?"), reply in natural, polite Roman Urdu.
   - If English (e.g. "What are your packages?", "Where are you located?"), reply in clear, natural English.
   - If Urdu script, reply in proper Urdu script.
5. UNANSWERED INTENTS: If the customer asks for information that is NOT mentioned anywhere in the Knowledge Base (e.g., an unlisted phone number or email), reply politely in their exact language:
   - English: "Our team has not listed this specific detail in our Knowledge Base yet, but you can chat with us right here or share your contact number so we can reach out!"
   - Roman Urdu: "Yeh detail filhal hamare Knowledge Base mein listed nahi hai, lekin aap yahan chat par hum se rabta kar sakte hain ya apna number share kar sakte hain!"
6. APPOINTMENTS & LEADS: If the customer expresses intent to book a consultation or appointment, guide them warmly to share their Name and Contact Number.

Knowledge base:
{kb_text}

Respond with ONLY a JSON object in this exact shape:
{{"reply": "<short conversational message>", "booking_ready": <true or false>, "booking_info": {{"name": "<or null>", "contact": "<or null>", "preferred_time": "<or null>", "notes": "<or null>"}}}}
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
    groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    return not bool(groq_key or gemini_key or openai_key)


def call_groq(api_key: str, messages: list):
    import httpx

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    payload = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }
    res = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    res_json = res.json()
    if "error" in res_json:
        raise Exception(res_json["error"].get("message", "Groq API error"))
    return res_json["choices"][0]["message"]["content"]


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
                    temperature=0.2,
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
                        "temperature": 0.2,
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
    groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()

    if groq_key:
        try:
            return call_groq(groq_key, messages)
        except Exception as err:
            print(f"[Groq LLM Warning] {err}")

    if gemini_key and not gemini_key.startswith("sk-"):
        try:
            return call_gemini(gemini_key, messages)
        except Exception as err:
            err_msg = str(err)
            print(f"[Gemini LLM Warning] {err_msg}")

    if openai_key and openai_key.startswith("sk-"):
        try:
            from openai import OpenAI

            client = OpenAI(api_key=openai_key)
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as err:
            print(f"[OpenAI LLM Warning] {err}")

    return None


import re

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "from", "of", "with", "by", "about",
    "against", "between", "into", "through", "during", "before", "after",
    "above", "below", "up", "down", "out", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "what", "which", "who", "whom", "whose", "your", "you", "yours",
    "my", "me", "mine", "our", "us", "ours", "it", "its", "this", "that",
    "these", "those", "am", "do", "does", "did", "doing", "would", "should",
    "could", "ought", "i", "we", "he", "she", "they", "them", "his", "her",
    "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "can", "will", "just", "now", "tell", "give",
    "show", "please", "kya", "hai", "hain", "ko", "se", "me", "mein", "ka",
    "ki", "ke", "par", "batao", "bataen", "bata", "karo", "do", "apka",
    "aap", "hum", "yeh", "woh", "sakte", "karte", "hoga", "hogi"
}

GREETING_PATTERNS = [
    "salam", "assalam", "asslam", "alaikum", "alikom", "alaik", "aoa",
    "slaam", "slm", "salm", "aslam", "hi", "hello", "hey", "hy",
    "greetings", "kaise ho", "kasay ho", "kia haal", "kya haal"
]


def is_greeting_message(query_clean: str) -> bool:
    clean = query_clean.lower()
    return any(p in clean for p in GREETING_PATTERNS)


def extract_tokens(text: str) -> set:
    words = re.findall(r'\w+', text.lower())
    return set(w for w in words if w not in STOPWORDS and len(w) > 1)


def calculate_similarity_score(query_tokens: set, query_text: str, question_text: str, answer_text: str) -> float:
    if not query_tokens:
        return 0.0

    q_text_clean = question_text.lower()
    a_text_clean = answer_text.lower()
    full_entry_text = q_text_clean + " " + a_text_clean
    entry_tokens = extract_tokens(full_entry_text)

    # 1. Exact phrase in question or answer
    if query_text in q_text_clean:
        return 10.0
    if query_text in a_text_clean:
        return 8.0

    # 2. Token overlap & Stem matching
    matched_count = 0
    question_matched_count = 0
    question_tokens = extract_tokens(q_text_clean)

    for qt in query_tokens:
        stem = qt[:4] if len(qt) >= 4 else qt
        if qt in entry_tokens or qt in full_entry_text or stem in full_entry_text:
            matched_count += 1
            if qt in question_tokens or qt in q_text_clean or stem in q_text_clean:
                question_matched_count += 1

    if matched_count == 0:
        return 0.0

    overlap_score = matched_count / len(query_tokens)
    score = (overlap_score * 5.0) + (question_matched_count * 3.0)
    return score


def find_relevant_kb_entries(kb_entries, new_message: str, max_results: int = 3):
    """Finds top N relevant KB entries sorted by semantic similarity score."""
    if not kb_entries or not new_message.strip():
        return []

    query_raw = new_message.strip()
    query_clean = re.sub(r'[^\w\s]', '', query_raw.lower()).strip()
    if not query_clean:
        return []

    query_tokens = extract_tokens(query_clean)
    scored_entries = []

    for e in kb_entries:
        score = calculate_similarity_score(query_tokens, query_clean, e.question, e.answer)
        if score > 0.5:
            scored_entries.append((score, e))

    scored_entries.sort(key=lambda x: x[0], reverse=True)
    return [entry for score, entry in scored_entries[:max_results]]


def find_best_kb_entry(kb_entries, new_message: str):
    if not kb_entries or not new_message.strip():
        return None

    query_raw = new_message.strip()
    query_clean = re.sub(r'[^\w\s]', '', query_raw.lower()).strip()
    if not query_clean:
        return None

    query_tokens = extract_tokens(query_clean)

    # 1. Exact Question Match
    for e in kb_entries:
        q_clean = re.sub(r'[^\w\s]', '', e.question.strip().lower())
        if q_clean == query_clean:
            return e

    # 2. Specific Keyword Synonyms (e.g. gmail/email/contact)
    query_words = query_clean.split()

    if any(w in query_clean for w in ["gmail", "email", "e-mail"]):
        for e in kb_entries:
            q_lower = e.question.lower()
            a_lower = e.answer.lower()
            if "@" in a_lower or "email" in q_lower or "gmail" in q_lower:
                return e

    # Short 1-2 Word Keyword Direct Search
    if len(query_words) <= 3:
        for word in query_words:
            if len(word) >= 3 and word not in STOPWORDS:
                stem = word[:4] if len(word) >= 4 else word
                for e in kb_entries:
                    q_text = e.question.lower()
                    a_text = e.answer.lower()
                    if word in q_text or word in a_text or stem in q_text or stem in a_text:
                        return e

    # 3. Substring Phrase Match
    for e in kb_entries:
        q_clean = e.question.strip().lower()
        if q_clean and (q_clean in query_clean or query_clean in q_clean):
            return e

    # 4. Token & Semantic Similarity Search with Threshold (>= 2.0)
    best_entry = None
    highest_score = 0.0

    for e in kb_entries:
        score = calculate_similarity_score(query_tokens, query_clean, e.question, e.answer)
        if score > highest_score:
            highest_score = score
            best_entry = e

    if best_entry and highest_score >= 2.0:
        return best_entry

    return None


def find_kb_match(kb_entries, new_message: str):
    entry = find_best_kb_entry(kb_entries, new_message)
    return entry.answer if entry else None


def generate_reply_with_custom_prompt(tenant_name: str, custom_prompt: str, kb_entries, history, new_message: str):
    best_entry = find_best_kb_entry(kb_entries, new_message)
    relevant_entries = find_relevant_kb_entries(kb_entries, new_message, max_results=3)
    kb_text = build_kb_text(kb_entries)

    query_clean = re.sub(r'[^\w\s]', '', new_message.strip().lower())

    # Handle Greetings & Pleasantries gracefully if no explicit greeting KB entry matched
    if is_greeting_message(query_clean) and not best_entry:
        is_roman_urdu = any(w in query_clean for w in ["salam", "assalam", "asslam", "aoa", "alaikum", "alikom", "slaam", "slm", "aslam"])
        greeting_reply = (
            "Walaikum Assalam! Main aap ki kya madad kar sakta hoon? Aap hamari services, pricing, ya location ke baare mein pooch sakte hain."
            if is_roman_urdu else
            f"Hello! Welcome to {tenant_name}. How can I assist you today? Feel free to ask about our services, pricing, or location!"
        )
        return {
            "reply": greeting_reply,
            "booking_ready": False,
            "booking_info": None,
        }

    # Build multi-entry context for LLM cross-extraction
    if relevant_entries:
        context_parts = []
        for idx, entry in enumerate(relevant_entries, 1):
            context_parts.append(f"Relevant Entry #{idx}:\nQuestion: {entry.question}\nAnswer: {entry.answer}")
        best_context = "\n\nMOST RELEVANT KNOWLEDGE BASE ENTRIES FOR THIS INTENT:\n" + "\n\n".join(context_parts) + "\n"
    elif best_entry:
        best_context = f"\n\nMOST RELEVANT KNOWLEDGE BASE ENTRY FOR THIS INTENT:\nQuestion: {best_entry.question}\nAnswer: {best_entry.answer}\n"
    else:
        best_context = ""

    if custom_prompt and custom_prompt.strip():
        base_prompt = custom_prompt.replace("{tenant_name}", tenant_name)
        system_prompt = f"{base_prompt}{best_context}\n\nMANDATORY LANGUAGE MATCHING & KNOWLEDGE BOUNDARY RULE:\n1. Always respond in the EXACT same language and script used by the customer in their message (Roman Urdu if Roman Urdu, English if English, Urdu if Urdu script).\n2. Answer strictly using ONLY the Knowledge Base below. Do not guess or extrapolate.\n\nFull Knowledge Base:\n{kb_text}\n\nRespond with ONLY a JSON object, no other text, in exactly this shape:\n{{\"reply\": \"<message to send back>\", \"booking_ready\": <true or false>, \"booking_info\": {{\"name\": \"<or null>\", \"contact\": \"<or null>\", \"preferred_time\": \"<or null>\", \"notes\": \"<or null>\"}}}}"
    else:
        system_prompt = (
            SYSTEM_PROMPT_TEMPLATE.format(tenant_name=tenant_name, kb_text=kb_text)
            + best_context
        )

    messages = build_messages(system_prompt, history, new_message)
    raw = call_llm(messages)

    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and parsed.get("reply"):
                reply_text = parsed["reply"]
                if not reply_text.startswith("[") and "Error" not in reply_text:
                    return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    # Direct Reliable Fallback: Return best matching KB entry answer!
    if best_entry:
        return {
            "reply": best_entry.answer,
            "booking_ready": False,
            "booking_info": None,
        }

    is_english = any(w in query_clean for w in ["what", "where", "how", "when", "why", "who", "which", "is", "are", "do", "can", "gmail", "email", "address", "phone"])
    fallback_reply = (
        "Thank you! This detail is currently not listed in our Knowledge Base, but you can chat with us right here or ask about our services and pricing!"
        if is_english else
        "Aap ka shukriya! Yeh jankari filhal mere paas nahi hai, hamari team jald aap se rabta karegi."
    )

    return {
        "reply": fallback_reply,
        "booking_ready": False,
        "booking_info": None,
    }


def generate_reply(tenant_name: str, kb_entries, history, new_message: str, custom_prompt: str = None):
    return generate_reply_with_custom_prompt(
        tenant_name=tenant_name,
        custom_prompt=custom_prompt or "",
        kb_entries=kb_entries,
        history=history,
        new_message=new_message
    )


EXTRACTION_SYSTEM_PROMPT = """You are a Strict Knowledge Base Q&A Extractor. 
Analyze the provided document text (PDF, Word, TXT, or CSV) and extract ONLY clean, high-quality Customer Question and Answer (Q&A) pairs.

STRICT EXTRACTION RULES:
1. EXTRACT ONLY REAL Q&A PAIRS: Extract strictly ONLY Customer Question and Answer pairs. IGNORE all document titles, author names, page numbers, intro disclaimers, copyright text, headers, footers, or filler text.
2. REFRAME SECTION TITLES INTO CUSTOMER QUESTIONS: Every "question" field MUST be phrased as a clear, natural customer question (e.g. "What are your services?", "What is the price of the Basic Package?", "Where is your office located?", "What are your clinic hours?"). If the document has headers or sections (like "Services" or "Pricing"), reframe them into proper customer questions!
3. COMPLETE FACTUAL ANSWERS: The "answer" field MUST contain only the exact factual answer corresponding to that specific question.
4. NO FILLER OR DUPLICATES: Do NOT extract generic headings as both question and answer. Do NOT extract non-Q&A sentences.

Respond with ONLY a JSON object in this exact structure:
{
  "qa_pairs": [
    {
      "question": "<Customer Question>",
      "answer": "<Exact Company Answer>"
    }
  ]
}
"""


def extract_qa_from_text(document_text: str) -> List[dict]:
    """RAG Document Chunker & Strict Q&A Extractor.
    Splits PDF / DOCX / TXT documents into individual, separate Knowledge Base Q&A entries."""
    if not document_text or not document_text.strip():
        return []

    import re

    # Clean raw document text
    text = document_text.replace("\r\n", "\n").replace("\r", "\n").strip()

    # Stage 1: Try AI LLM Extraction (Groq / Gemini / OpenAI)
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Document text to extract Q&A entries from:\n\n{text[:12000]}"}
    ]
    raw = call_llm(messages)

    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "qa_pairs" in parsed and isinstance(parsed["qa_pairs"], list):
                valid_llm_pairs = []
                for item in parsed["qa_pairs"]:
                    q = item.get("question", "").strip()
                    a = item.get("answer", "").strip()
                    if q and a and q.lower() != a.lower() and len(q) >= 3:
                        valid_llm_pairs.append({"question": q, "answer": a})
                if valid_llm_pairs:
                    return valid_llm_pairs
        except Exception:
            pass

    # Stage 2: Rule-Based Fallback Extraction
    extracted = []

    def reframe_into_question(t: str) -> str:
        t_clean = re.sub(r'^(q|question|\d+[\.\)]|\bfaqs?\b|section\s*\d+[:\.]?|[\•\-\*])\s*', '', t.strip(), flags=re.IGNORECASE).strip()
        t_clean = t_clean.rstrip(":").strip()
        if not t_clean:
            return "Company Information"

        if t_clean.endswith("?") or t_clean.lower().startswith(("what", "where", "how", "when", "why", "who", "which", "can", "do", "is", "are", "aap", "hamari")):
            return t_clean

        tl = t_clean.lower()
        if "location" in tl or "address" in tl:
            return "Where is your office located?"
        elif "service" in tl or "offer" in tl:
            return "What services do you offer?"
        elif "price" in tl or "pricing" in tl or "package" in tl or "cost" in tl or "fee" in tl:
            return "What are your prices and packages?"
        elif "time" in tl or "timing" in tl or "hours" in tl or "schedule" in tl:
            return "What are your business hours and timings?"
        elif "contact" in tl or "phone" in tl or "email" in tl or "number" in tl:
            return "How can I contact you?"

        return f"What is your information regarding {t_clean}?"

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    curr_q = None
    curr_ans = []

    for line in lines:
        is_header = (
            line.endswith("?") or
            bool(re.match(r'^(q[:\s]|\d+[\.\)]|\bfaqs?\b|section\s*\d+|[\•\-\*])', line, re.IGNORECASE)) or
            (":" in line and len(line.split(":")[0]) <= 60 and not line.startswith("http"))
        )
        if is_header:
            if curr_q:
                ans = "\n".join(curr_ans).strip()
                q_formatted = reframe_into_question(curr_q)
                if ans and q_formatted.lower() != ans.lower():
                    extracted.append({"question": q_formatted, "answer": ans})
                curr_ans = []

            if ":" in line and not line.endswith("?"):
                parts = line.split(":", 1)
                curr_q = parts[0]
                if parts[1].strip():
                    curr_ans.append(parts[1].strip())
            else:
                curr_q = line
        elif curr_q:
            curr_ans.append(line)
        else:
            curr_q = line

    if curr_q:
        ans = "\n".join(curr_ans).strip()
        q_formatted = reframe_into_question(curr_q)
        if ans and q_formatted.lower() != ans.lower():
            extracted.append({"question": q_formatted, "answer": ans})

    # Strategy C: Paragraph / Double-Newline Chunking
    if len(extracted) <= 1:
        paragraphs = [p.strip() for p in re.split(r'\n{2,}|\.\s{2,}', text) if p.strip()]
        if len(paragraphs) > 1:
            extracted = []
            for p in paragraphs:
                lines = [l.strip() for l in p.splitlines() if l.strip()]
                if len(lines) >= 2:
                    q = reframe_into_question(lines[0])
                    a = "\n".join(lines[1:])
                    extracted.append({"question": q[:120], "answer": a})
                else:
                    sentences = re.split(r'(?<=[.!?])\s+', p)
                    if len(sentences) >= 2:
                        extracted.append({
                            "question": reframe_into_question(sentences[0][:120]),
                            "answer": " ".join(sentences[1:])
                        })
                    else:
                        extracted.append({
                            "question": reframe_into_question(p[:60]),
                            "answer": p
                        })

    valid_entries = []
    for item in extracted:
        q = item.get("question", "").strip()
        a = item.get("answer", "").strip()
        if q and a and q.lower() != a.lower():
            valid_entries.append({"question": q, "answer": a})

    return valid_entries if valid_entries else [{"question": "Company Information", "answer": text}]
