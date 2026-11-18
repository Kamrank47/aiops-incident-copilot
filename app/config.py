import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    # Flash-Lite: lowest-cost Gemini tier, fast, supports JSON schema output.
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    llm_timeout_s: float = float(os.getenv("LLM_TIMEOUT_S", "15"))
    prometheus_url: str = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
    loki_url: str = os.getenv("LOKI_URL", "http://loki:3100")
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    runbook_dir: str = os.getenv("RUNBOOK_DIR", "runbooks")
    max_log_lines: int = int(os.getenv("MAX_LOG_LINES", "20"))


def get_settings() -> Settings:
    return Settings()
