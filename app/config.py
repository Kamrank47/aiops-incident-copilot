import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: str = ".env") -> None:
    """Load KEY=VALUE lines into the environment without overriding real env vars."""
    f = Path(path)
    if not f.is_file():
        return
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    # "groq" (free tier, default) or "gemini".
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    # GPT-OSS 120B on Groq: free tier, fast, supports JSON mode.
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
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
