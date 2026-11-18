import json

import httpx

from .config import Settings
from .models import Triage

SYSTEM_PROMPT = (
    "You are an SRE assistant triaging a production alert. Use ONLY the supplied "
    "alert, metrics, logs and runbook. If evidence is weak, say so and set "
    "confidence to low. Never invent metrics. Suggest read-only diagnostic steps "
    "before any change. Keep every field short."
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING"},
        "likely_cause": {"type": "STRING"},
        "confidence": {"type": "STRING", "enum": ["low", "medium", "high"]},
        "next_steps": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["summary", "likely_cause", "confidence", "next_steps"],
}


async def call_llm(prompt: str, s: Settings) -> Triage:
    """Ask Gemini for a structured triage. Raises on any failure."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{s.gemini_model}:generateContent"
    )
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 600,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }
    async with httpx.AsyncClient(timeout=s.llm_timeout_s) as client:
        r = await client.post(url, json=body, headers={"x-goog-api-key": s.gemini_api_key})
        r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return Triage(**json.loads(text), source="llm")
