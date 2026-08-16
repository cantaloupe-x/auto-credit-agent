import pytest
from fastapi.testclient import TestClient

from backend.app import create_app


VALID_APPLICATION = {
    "name": "测试申请人",
    "city": "上海市",
    "occupation": "企业职员",
    "vehicle_model": "测试车辆",
    "vehicle_source": "4S 店新车",
    "income": 20000,
    "monthly_debt": 3000,
    "vehicle_price": 200000,
    "down_payment": 80000,
    "loan_amount": 120000,
    "loan_term": 36,
    "work_years": 5,
    "recent_overdue": False,
    "authorized": True,
}


def test_health_and_seed_applications(tmp_path):
    with TestClient(create_app(tmp_path / "test.db")) as client:
        frontend = client.get("/")
        assert client.get("/api/health").json() == {
            "status": "ok",
            "database": "ok",
        }
        applications = client.get("/api/applications").json()

    assert frontend.status_code == 200
    assert "车贷智审" in frontend.text
    assert len(applications) == 2
    assert applications[0]["model_version"] == "rule-v1.0"


def test_application_persists_after_restart(tmp_path):
    database = tmp_path / "test.db"
    with TestClient(create_app(database)) as client:
        response = client.post("/api/applications", json=VALID_APPLICATION)
        assert response.status_code == 201
        application_id = response.json()["id"]

    with TestClient(create_app(database)) as client:
        application = client.get(f"/api/applications/{application_id}").json()

    assert application["name"] == "测试申请人"
    assert application["score"] == 100
    assert application["status"] == "pending_review"


def test_manual_review_and_audit_trail(tmp_path):
    with TestClient(create_app(tmp_path / "test.db")) as client:
        created = client.post("/api/applications", json=VALID_APPLICATION).json()
        application_id = created["id"]
        response = client.patch(
            f"/api/applications/{application_id}/review",
            json={
                "decision": "rejected",
                "comment": "负债材料仍需进一步核实",
                "reviewer": "林晓雯",
            },
        )
        events = client.get(f"/api/applications/{application_id}/audit").json()

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["review_comment"] == "负债材料仍需进一步核实"
    assert [event["event_type"] for event in events] == [
        "application_submitted",
        "risk_assessed",
        "manual_reviewed",
    ]
    assert events[-1]["details"]["decision"] == "rejected"


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    [
        ("approved", "approved"),
        ("needs_more_info", "needs_more_info"),
        ("rejected", "rejected"),
    ],
)
def test_review_decision_is_preserved(tmp_path, decision, expected_status):
    with TestClient(create_app(tmp_path / f"{decision}.db")) as client:
        application_id = client.post(
            "/api/applications", json=VALID_APPLICATION
        ).json()["id"]
        response = client.patch(
            f"/api/applications/{application_id}/review",
            json={"decision": decision, "comment": "人工复核测试"},
        )

    assert response.json()["status"] == expected_status


def test_invalid_application_and_missing_case(tmp_path):
    with TestClient(create_app(tmp_path / "test.db")) as client:
        invalid = {**VALID_APPLICATION, "authorized": False}
        assert client.post("/api/applications", json=invalid).status_code == 422
        assert client.get("/api/applications/not-found").status_code == 404
        assert (
            client.patch(
                "/api/applications/not-found/review",
                json={"decision": "approved", "comment": "资料一致"},
            ).status_code
            == 404
        )


def test_stateless_assessment_endpoint(tmp_path):
    with TestClient(create_app(tmp_path / "test.db")) as client:
        response = client.post("/api/applications/assess", json=VALID_APPLICATION)

    assert response.status_code == 200
    assert response.json()["assessment"]["score"] == 100
