"""确定性 Agent 工作流：规则评分 -> 检索 -> 解释 -> 补件 -> 人工确认。"""

import hashlib
import json
from typing import Dict

from .domain import WORKFLOW_VERSION
from .knowledge import retrieve_knowledge
from .risk_engine import assess
from .schemas import AgentRequest, AgentResponse, KnowledgeCitation


def _dump_model(model) -> Dict[str, object]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def _trace_id(payload: Dict[str, object]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "trace-" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]


def run_agent(request: AgentRequest) -> AgentResponse:
    application = _dump_model(request.application)
    assessment = assess(application)
    entries = retrieve_knowledge(assessment, request.missing_documents, request.knowledge_version)
    citations = [KnowledgeCitation(knowledge_id=e["id"], title=e["title"], version=e["version"], excerpt=e["guidance"]) for e in entries]

    requested = list(dict.fromkeys(request.missing_documents))
    for entry in entries:
        for document in entry.get("required_documents", []):
            if document not in requested:
                requested.append(document)

    explanation = "；".join(assessment["reasons"])
    explanation += "。以上分数由固定规则生成；Agent 仅结合版本化知识说明风险。"
    trace_payload = {"application": application, "missing_documents": request.missing_documents, "knowledge_version": request.knowledge_version}
    return AgentResponse(
        trace_id=request.trace_id or _trace_id(trace_payload),
        rule_assessment=assessment,
        risk_explanation=explanation,
        citations=citations,
        requested_documents=requested,
    )
