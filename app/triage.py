import json

from .config import Settings
from .context import gather_context, load_runbook
from .llm import call_llm
from .models import Alert, Context, Triage
from .redact import redact


def build_prompt(alert: Alert, ctx: Context, runbook: str) -> str:
    prompt = json.dumps(
        {
            "alert": {"labels": alert.labels, "annotations": alert.annotations},
            "metrics": ctx.metrics,
            "error_logs": ctx.log_lines,
            "recent_deploys": ctx.recent_deploys,
            "runbook": runbook,
        },
        indent=2,
    )
    return redact(prompt)


def fallback(alert: Alert) -> Triage:
    """Used when the LLM is unavailable: surface the raw alert, never go silent."""
    name = alert.labels.get("alertname", "unknown alert")
    return Triage(
        summary=f"{name}: {alert.annotations.get('summary', 'no summary')}",
        likely_cause="LLM triage unavailable; see raw alert.",
        confidence="low",
        next_steps=["Check the alert's runbook and dashboards manually."],
        source="fallback",
    )


async def triage_alert(alert: Alert, s: Settings) -> Triage:
    ctx = await gather_context(alert, s)
    runbook = load_runbook(alert.labels.get("alertname", ""), s.runbook_dir)
    try:
        return await call_llm(build_prompt(alert, ctx, runbook), s)
    except Exception:
        return fallback(alert)
