import pytest

from app.redact import redact


@pytest.mark.parametrize(
    ("raw", "must_not_contain"),
    [
        ("key AKIAABCDEFGHIJKLMNOP leaked", "AKIAABCDEFGHIJKLMNOP"),
        ("Authorization: Bearer abc.def-123", "abc.def-123"),
        ("db password=hunter2 failed", "hunter2"),
        ("user bob@example.com timed out", "bob@example.com"),
        ("connect to 10.0.3.17 refused", "10.0.3.17"),
    ],
)
def test_redact_removes_sensitive_values(raw: str, must_not_contain: str) -> None:
    assert must_not_contain not in redact(raw)


def test_redact_keeps_normal_text() -> None:
    assert redact("upstream timeout after 30s") == "upstream timeout after 30s"
