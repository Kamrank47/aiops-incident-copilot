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
    """Ask the configured provider for a structured triage. Raises on any failure."""
    if s.llm_provider == "groq":
        return await _call_groq(prompt, s)
    return await _call_gemini(prompt, s)


JSON_INSTRUCTION = (
    ' Reply with a single JSON object with keys "summary" (string), '
    '"likely_cause" (string), "confidence" ("low", "medium" or "high") and '
    '"next_steps" (array of strings).'
)


async def _call_groq(prompt: str, s: Settings) -> Triage:
    body = {
        "model": s.groq_model,
        "temperature": 0.1,
        "max_tokens": 1500,
        "reasoning_effort": "low",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT + JSON_INSTRUCTION},
            {"role": "user", "content": prompt},
        ],
    }
    async with httpx.AsyncClient(timeout=s.llm_timeout_s) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=body,
            headers={"Authorization": f"Bearer {s.groq_api_key}"},
        )
        r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    return Triage(**json.loads(text), source="llm")


async def _call_gemini(prompt: str, s: Settings) -> Triage:
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
