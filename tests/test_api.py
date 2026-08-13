import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


APPLICATION = {"name": "测试申请人", "income": 20000, "monthly_debt": 3000, "vehicle_price": 200000, "down_payment": 80000, "loan_amount": 120000}


def test_existing_assess_api_contract_is_preserved():
    response = client.post("/api/applications/assess", json=APPLICATION)
    assert response.status_code == 200
    assert set(response.json()) == {"application", "assessment"}
    assert response.json()["assessment"]["model_version"] == "rule-v1.0"


def test_agent_api_and_metadata_contract():
    metadata = client.get("/api/agent/metadata")
    assert metadata.status_code == 200
    assert metadata.json()["model_api_required"] is False
    assert metadata.json()["fictional_test_data"] is True

    response = client.post("/api/agent/evaluate", json={"application": APPLICATION})
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "agent-schema-v1.0"
    assert body["human_decision"] == "pending"


def test_applicant_dataset_remains_list_and_is_explicitly_fictional():
    response = client.get("/api/applications")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 15
    assert all(item["fictional_test_data"] is True for item in response.json())


def test_unknown_knowledge_version_returns_422():
    response = client.post("/api/agent/evaluate", json={"application": APPLICATION, "knowledge_version": "missing-v9"})
    assert response.status_code == 422


def test_invalid_application_fields_return_422():
    invalid_payloads = [
        {**APPLICATION, "name": "  "},
        {**APPLICATION, "income": 0},
        {**APPLICATION, "vehicle_price": 0},
        {**APPLICATION, "monthly_debt": -1},
        {**APPLICATION, "down_payment": -1},
        {**APPLICATION, "loan_amount": -1},
        {**APPLICATION, "work_years": -1},
        {**APPLICATION, "loan_term": 5},
        {**APPLICATION, "loan_term": 85},
    ]
    for payload in invalid_payloads:
        assess_response = client.post("/api/applications/assess", json=payload)
        agent_response = client.post("/api/agent/evaluate", json={"application": payload})
        assert assess_response.status_code == 422, payload
        assert agent_response.status_code == 422, payload
