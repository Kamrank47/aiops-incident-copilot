import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"(?i)bearer\s+[a-z0-9._\-]+"), "Bearer [REDACTED]"),
    (
        re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)(\s*[=:]\s*)\S+"),
        r"\1\2[REDACTED]",
    ),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"), "[REDACTED_IP]"),
]


def redact(text: str) -> str:
    """Strip secrets and obvious PII before text leaves the network."""
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text
