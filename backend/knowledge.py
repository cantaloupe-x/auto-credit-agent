"""本地、版本固定且可复现的风控知识检索。"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from .domain import DEFAULT_KNOWLEDGE_VERSION


KNOWLEDGE_ROOT = Path(__file__).parents[1] / "knowledge"


def load_knowledge(version: Optional[str] = None) -> Dict[str, object]:
    selected = version or DEFAULT_KNOWLEDGE_VERSION
    path = KNOWLEDGE_ROOT / selected / "knowledge.json"
    if not path.exists():
        raise ValueError("未知知识库版本: %s" % selected)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != selected:
        raise ValueError("知识库目录与内容版本不一致")
    return payload


def retrieve_knowledge(assessment: Dict[str, object], missing_documents: List[str], version: Optional[str] = None, limit: int = 8) -> List[Dict[str, str]]:
    payload = load_knowledge(version)
    query = " ".join(list(assessment.get("reasons", [])) + missing_documents)
    scored = []
    for position, item in enumerate(payload["entries"]):
        score = sum(1 for keyword in item["keywords"] if keyword in query)
        if item.get("always_include"):
            score += 1
        if score:
            scored.append((-score, position, item))
    scored.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in scored[:limit]]
