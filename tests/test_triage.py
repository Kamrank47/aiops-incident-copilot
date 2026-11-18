import pytest
from fastapi.testclient import TestClient

from app import main, triage
from app.config import Settings
from app.models import Alert, Context, Triage


def _alert() -> Alert:
    return Alert(
        labels={"alertname": "HighErrorRate", "service": "checkout"},
        annotations={"summary": "5xx rate above 0.5/s"},
    )


def test_prompt_is_redacted() -> None:
    ctx = Context(log_lines=["login failed password=hunter2 from 10.1.2.3"])
    prompt = triage.build_prompt(_alert(), ctx, "")
    assert "hunter2" not in prompt
    assert "10.1.2.3" not in prompt


async def test_llm_failure_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_ctx(alert: Alert, s: Settings) -> Context:
        return Context()

    async def boom(prompt: str, s: Settings) -> Triage:
        raise RuntimeError("llm down")

    monkeypatch.setattr(triage, "gather_context", fake_ctx)
    monkeypatch.setattr(triage, "call_llm", boom)
    result = await triage.triage_alert(_alert(), Settings())
    assert result.source == "fallback"
    assert result.confidence == "low"


def test_webhook_skips_resolved_alerts(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_triage(alert: Alert, s: Settings) -> Triage:
        return triage.fallback(alert)

    monkeypatch.setattr(main, "triage_alert", fake_triage)
    client = TestClient(main.app)
    body = {
        "alerts": [
            {"status": "resolved", "labels": {"alertname": "A"}},
            {"status": "firing", "labels": {"alertname": "B"}},
        ]
    }
    resp = client.post("/webhook", json=body)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
