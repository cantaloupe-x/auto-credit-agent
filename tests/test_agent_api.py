"""PR #1 的 Agent / 评估接口测试。

合并说明：这些用例原本在 tests/test_api.py 里，用模块级 TestClient(app)。
PR #2 把后端改成了 create_app() 工厂加 SQLite，所以这里改用临时库的 fixture，
避免测试之间互相污染，断言本身保持不变——只有 test_applications_endpoint_contract
一条按合并后的接口契约重写了，原因见该函数的注释。
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app


ROOT = Path(__file__).parents[1]

APPLICATION = {
    "name": "测试申请人",
    "income": 20000,
    "monthly_debt": 3000,
    "vehicle_price": 200000,
    "down_payment": 80000,
    "loan_amount": 120000,
}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "agent.db")) as test_client:
        yield test_client


def test_existing_assess_api_contract_is_preserved(client):
    response = client.post("/api/applications/assess", json=APPLICATION)
    assert response.status_code == 200
    assert set(response.json()) == {"application", "assessment"}
    assert response.json()["assessment"]["model_version"] == "rule-v1.0"


def test_agent_api_and_metadata_contract(client):
    metadata = client.get("/api/agent/metadata")
    assert metadata.status_code == 200
    assert metadata.json()["model_api_required"] is False
    assert metadata.json()["fictional_test_data"] is True

    response = client.post("/api/agent/evaluate", json={"application": APPLICATION})
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "agent-schema-v1.0"
    assert body["human_decision"] == "pending"


def test_applications_endpoint_contract(client):
    """合并后 /api/applications 返回数据库里的案件队列，不再返回评估数据集。

    PR #1 原来断言这个端点至少返回 15 条、且每条都带 fictional_test_data，
    那是基于它把 data/applicants.json 当成评估数据集来直接返回。
    PR #2 之后这个端点是前端队列的数据源（要带 city / vehicle_model 等展示字段），
    两种契约不能共存，这里保留 PR #2 的。虚构评估数据集的断言移到下面一条。
    """
    response = client.get("/api/applications")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all(item["model_version"] == "rule-v1.0" for item in response.json())


def test_evaluation_dataset_is_explicitly_fictional():
    payload = json.loads((ROOT / "data" / "agent_eval_cases.json").read_text(encoding="utf-8"))
    assert payload["fictional_test_data"] is True
    assert len(payload["cases"]) >= 15


def test_unknown_knowledge_version_returns_422(client):
    response = client.post(
        "/api/agent/evaluate",
        json={"application": APPLICATION, "knowledge_version": "missing-v9"},
    )
    assert response.status_code == 422


def test_invalid_application_fields_return_422(client):
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
