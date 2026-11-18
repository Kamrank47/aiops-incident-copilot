import httpx
from fastapi import FastAPI
from prometheus_client import Counter, make_asgi_app

from .config import get_settings
from .models import Alert, AlertmanagerPayload, Triage
from .triage import triage_alert

app = FastAPI(title="aiops-incident-copilot")
app.mount("/metrics", make_asgi_app())

TRIAGES = Counter("triage_total", "Triages produced", ["source", "confidence"])


async def post_to_slack(alert: Alert, t: Triage, url: str) -> None:
    text = (
        f"*{alert.labels.get('alertname', 'alert')}* ({alert.labels.get('service', '?')})\n"
        f"{t.summary}\n*Likely cause:* {t.likely_cause} (confidence: {t.confidence})\n"
        + "\n".join(f"• {step}" for step in t.next_steps)
    )
    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(url, json={"text": text})


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(payload: AlertmanagerPayload) -> list[Triage]:
    s = get_settings()
    results: list[Triage] = []
    for alert in payload.alerts:
        if alert.status != "firing":
            continue
        t = await triage_alert(alert, s)
        TRIAGES.labels(source=t.source, confidence=t.confidence).inc()
        if s.slack_webhook_url:
            try:
                await post_to_slack(alert, t, s.slack_webhook_url)
            except Exception:
                pass  # notification failure must not fail the webhook
        results.append(t)
    return results
