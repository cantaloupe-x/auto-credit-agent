import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_versioned_knowledge_is_explicitly_fictional():
    payload = json.loads((ROOT / "knowledge" / "risk-knowledge-v1.0" / "knowledge.json").read_text(encoding="utf-8"))
    assert payload["version"] == "risk-knowledge-v1.0"
    assert payload["fictional_test_data"] is True
    assert all(item["version"] == payload["version"] for item in payload["entries"])
    ids = {item["id"] for item in payload["entries"]}
    assert {"KB-AMOUNT-001", "KB-TERM-001", "KB-COMPLETE-001", "KB-INCOME-001", "KB-DUPLICATE-001", "KB-CONSENT-001"} <= ids


def test_gitignore_covers_generated_python_and_secrets():
    content = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("__pycache__/", ".pytest_cache/", ".venv/", ".env"):
        assert pattern in content
