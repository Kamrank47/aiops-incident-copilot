# aiops-incident-copilot

Alertmanager sends a firing alert to this service. The service pulls context from Prometheus and Loki, adds the matching runbook, and asks a hosted LLM for a short triage. The result goes to Slack.

```mermaid
flowchart LR
  P[Prometheus] --> AM[Alertmanager]
  AM -->|webhook| API[FastAPI triage service]
  API --> PQ[Prometheus query API]
  API --> L[Loki query API]
  API --> R[Runbooks]
  API -->|redacted prompt| LLM[GPT-OSS 120B on Groq]
  API --> S[Slack]
  API --> M[/metrics]
```

## Design decisions

- **Model:** `openai/gpt-oss-120b` on Groq, which has a free tier and fast inference. Triage prompts are short, so latency is low. Set `GROQ_MODEL` to change it, or `LLM_PROVIDER=gemini` to use Gemini instead.
- **Structured output:** JSON mode plus Pydantic validation (`summary`, `likely_cause`, `confidence`, `next_steps`), so responses are always parseable or rejected.
- **Read-only:** the service only suggests steps. It never runs commands against your systems.
- **Redaction:** secrets, emails, IPs and tokens are stripped before any text leaves the network ([`app/redact.py`](app/redact.py)).
- **Never silent:** if the LLM fails or times out, the raw alert is still sent with `source: fallback`.
- **Hardened container:** non-root, read-only filesystem, all capabilities dropped, Trivy scan in CI.

## Run it

```bash
cp .env.example .env        # add GROQ_API_KEY (and optionally SLACK_WEBHOOK_URL)
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
GROQ_API_KEY=... python -m eval.run
```

Results with `openai/gpt-oss-120b` on Groq (free tier):

| scenario | correct | confidence | latency |
|---|---|---|---|
| deploy-regression | yes | high | 1.2s |
| memory-leak-oom | yes | high | 1.1s |
| db-connection-exhaustion | yes | medium | 1.0s |
| upstream-dependency | yes | medium | 1.2s |
| probe-misconfig | yes | medium | 1.3s |

Top-line accuracy: 5/5. This is a small, keyword-scored set of synthetic scenarios, so treat it as a smoke test, not a benchmark.

## Limits

- Context queries assume a `service` label and common metric names. Edit `METRIC_QUERIES` in [`app/context.py`](app/context.py) for your setup.
- `recent_deploys` is empty until you wire in Argo CD or your git history.
- The keyword scoring in the eval is a rough check. Review the actual responses too.
