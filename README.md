# aiops-incident-copilot

Alertmanager sends a firing alert to this service. The service pulls context from Prometheus and Loki, adds the matching runbook, and asks a hosted LLM for a short triage. The result goes to Slack.

```mermaid
flowchart LR
  P[Prometheus] --> AM[Alertmanager]
  AM -->|webhook| API[FastAPI triage service]
  API --> PQ[Prometheus query API]
  API --> L[Loki query API]
  API --> R[Runbooks]
  API -->|redacted prompt| LLM[Gemini 2.5 Flash-Lite]
  API --> S[Slack]
  API --> M[/metrics]
```

## Design decisions

- **Model:** `gemini-2.5-flash-lite`. It is among the cheapest hosted models. Triage prompts are short, so latency is low and the cost per alert is a fraction of a cent. Set `GEMINI_MODEL` to change it.
- **Structured output:** the API enforces a JSON schema (`summary`, `likely_cause`, `confidence`, `next_steps`), so responses are always parseable.
- **Read-only:** the service only suggests steps. It never runs commands against your systems.
- **Redaction:** secrets, emails, IPs and tokens are stripped before any text leaves the network ([`app/redact.py`](app/redact.py)).
- **Never silent:** if the LLM fails or times out, the raw alert is still sent with `source: fallback`.
- **Hardened container:** non-root, read-only filesystem, all capabilities dropped, Trivy scan in CI.

## Run it

```bash
cp .env.example .env        # add GEMINI_API_KEY (and optionally SLACK_WEBHOOK_URL)
docker compose up --build
```

Send a test alert:

```bash
curl -s localhost:8000/webhook -H 'content-type: application/json' -d '{
  "alerts": [{"status": "firing",
    "labels": {"alertname": "HighErrorRate", "service": "checkout"},
    "annotations": {"summary": "5xx rate above 0.5/s"}}]}'
```

## Develop

```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check . && pytest
```

## Evaluation

[`eval/scenarios.json`](eval/scenarios.json) holds fault scenarios with a known root cause. Run them against the live model:

```bash
GEMINI_API_KEY=... python -m eval.run
```

Results (fill in after your first run):

| scenario | correct | confidence | latency |
|---|---|---|---|
| _run the eval and paste the table here_ | | | |

## Limits

- Context queries assume a `service` label and common metric names. Edit `METRIC_QUERIES` in [`app/context.py`](app/context.py) for your setup.
- `recent_deploys` is empty until you wire in Argo CD or your git history.
- The keyword scoring in the eval is a rough check. Review the actual responses too.
