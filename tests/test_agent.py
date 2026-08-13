import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.agent import run_agent
from backend.schemas import AgentRequest


ROOT = Path(__file__).parents[1]


def request_for(application, **kwargs):
    return AgentRequest(application=application, **kwargs)


def dump_model(model):
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def test_agent_is_deterministic_and_requires_no_model_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    application = {"name": "测试申请人", "income": 20000, "monthly_debt": 14000, "vehicle_price": 300000, "down_payment": 40000, "loan_amount": 260000, "work_years": 0.5, "recent_overdue": True}
    first = dump_model(run_agent(request_for(application)))
    second = dump_model(run_agent(request_for(application)))
    assert first == second
    assert first["mode"] == "deterministic"
    assert first["human_decision"] == "pending"
    assert first["next_action"] == "提交人工复核"


def test_agent_preserves_rule_score_and_retrieves_grounding():
    application = {"name": "测试申请人", "income": 20000, "monthly_debt": 14000, "vehicle_price": 300000, "down_payment": 40000, "loan_amount": 260000, "work_years": 0.5, "recent_overdue": True}
    result = dump_model(run_agent(request_for(application)))
    assert result["rule_assessment"]["score"] == 35
    citation_ids = {item["knowledge_id"] for item in result["citations"]}
    assert {"KB-DTI-001", "KB-DOWN-001", "KB-WORK-001", "KB-OVERDUE-001"} <= citation_ids
    assert "最终决定必须由人工确认" in result["disclaimer"]


def test_eval_dataset_contract():
    dataset = json.loads((ROOT / "data" / "agent_eval_cases.json").read_text(encoding="utf-8"))
    assert dataset["fictional_test_data"] is True
    assert len(dataset["cases"]) >= 10
    for case in dataset["cases"]:
        expected_error = case.get("expected_error")
        if expected_error == "validation_error":
            with pytest.raises(ValidationError):
                request_for(case["application"])
            continue
        request = request_for(
            case["application"],
            missing_documents=case.get("missing_documents", []),
            knowledge_version=case.get("knowledge_version"),
        )
        if expected_error == "unknown_knowledge_version":
            with pytest.raises(ValueError, match="未知知识库版本"):
                run_agent(request)
            continue
        output = dump_model(run_agent(request))
        expected = case["expected"]
        if "min_score" in expected:
            assert output["rule_assessment"]["score"] >= expected["min_score"]
        if "max_score" in expected:
            assert output["rule_assessment"]["score"] <= expected["max_score"]
        assert output["human_decision"] == expected["human_decision"]
        citation_ids = {item["knowledge_id"] for item in output["citations"]}
        assert set(expected.get("citation_ids", [])) <= citation_ids
        assert set(expected.get("requested_documents", [])) <= set(output["requested_documents"])
        if "reason_contains" in expected:
            assert expected["reason_contains"] in " ".join(output["rule_assessment"]["reasons"])


def test_unknown_knowledge_version_fails_closed():
    application = {"name": "测试申请人", "income": 20000, "monthly_debt": 3000, "vehicle_price": 200000, "down_payment": 80000, "loan_amount": 120000}
    try:
        run_agent(request_for(application, knowledge_version="missing-v9"))
    except ValueError as exc:
        assert "未知知识库版本" in str(exc)
    else:
        raise AssertionError("unknown knowledge version must fail")


def test_amount_mismatch_is_scored_by_rules_and_explained_by_agent():
    application = {"name": "虚构金额不一致案例", "income": 25000, "monthly_debt": 3000, "vehicle_price": 250000, "down_payment": 50000, "loan_amount": 150000}
    result = dump_model(run_agent(request_for(application)))
    assert result["rule_assessment"]["score"] == 90
    assert any("金额之和同车辆价格不一致" in reason for reason in result["rule_assessment"]["reasons"])
    assert "KB-AMOUNT-001" in {item["knowledge_id"] for item in result["citations"]}
    assert result["human_decision"] == "pending"
