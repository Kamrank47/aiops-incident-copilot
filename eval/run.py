"""Run fault scenarios through the live LLM and score root-cause hits.

Usage: GEMINI_API_KEY=... python -m eval.run
A scenario passes when the likely cause or summary mentions an expected keyword.
Output is a markdown table you can paste into the README.
"""

import asyncio
import json
import time
from pathlib import Path

from app.config import get_settings
from app.llm import call_llm
from app.models import Alert, Context
from app.triage import build_prompt, load_runbook


async def main() -> None:
    s = get_settings()
    scenarios = json.loads((Path(__file__).parent / "scenarios.json").read_text())
    rows, hits = [], 0
    for sc in scenarios:
        alert = Alert(**sc["alert"])
        ctx = Context(**sc["context"])
        runbook = load_runbook(alert.labels["alertname"], s.runbook_dir)
        start = time.perf_counter()
        t = await call_llm(build_prompt(alert, ctx, runbook), s)
        elapsed = time.perf_counter() - start
        text = f"{t.summary} {t.likely_cause}".lower()
        ok = any(k in text for k in sc["expected_keywords"])
        hits += ok
        rows.append(f"| {sc['id']} | {'yes' if ok else 'no'} | {t.confidence} | {elapsed:.1f}s |")
    print("| scenario | correct | confidence | latency |\n|---|---|---|---|")
    print("\n".join(rows))
    print(f"\nTop-line accuracy: {hits}/{len(scenarios)}")


if __name__ == "__main__":
    asyncio.run(main())
