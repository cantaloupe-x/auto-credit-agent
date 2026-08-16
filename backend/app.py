from datetime import datetime
from pathlib import Path
import json
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .risk_engine import assess

ROOT = Path(__file__).parents[1]
DATA = ROOT / "data" / "applicants.json"
ASSESSMENTS = ROOT / "data" / "assessments.json"
AUDIT_LOGS = ROOT / "data" / "audit_logs.json"

app = FastAPI(title="Auto Credit Agent API")


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_applications():
    return read_json(DATA, [])


def save_applications(items):
    write_json(DATA, items)


def load_assessments():
    return read_json(ASSESSMENTS, [])


def save_assessments(items):
    write_json(ASSESSMENTS, items)


def load_audit_logs():
    return read_json(AUDIT_LOGS, [])


def save_audit_logs(items):
    write_json(AUDIT_LOGS, items)


def find_application(app_id: str):
    items = load_applications()
    for index, item in enumerate(items):
        if item["id"] == app_id:
            return items, index, item
    raise HTTPException(status_code=404, detail="Application not found")


def latest_assessments_by_app():
    by_app = {}
    for assessment in load_assessments():
        app_id = assessment["application_id"]
        existing = by_app.get(app_id)
        if not existing or assessment.get("assessed_at", "") > existing.get("assessed_at", ""):
            by_app[app_id] = assessment
    return by_app


def enrich_applications(items):
    assessments = latest_assessments_by_app()
    enriched = []
    for item in items:
        record = dict(item)
        assessment = assessments.get(item["id"])
        if assessment:
            record["assessment"] = {
                key: value for key, value in assessment.items() if key != "application_id"
            }
        enriched.append(record)
    return enriched


class LoanApplication(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    income: float = Field(gt=0)
    monthly_debt: float = Field(ge=0)
    vehicle_price: float = Field(gt=0)
    down_payment: float = Field(ge=0)
    loan_amount: float = Field(gt=0)
    loan_term: int = Field(default=36, ge=6, le=84)
    work_years: float = Field(default=3, ge=0, le=60)
    recent_overdue: bool = False


class Decision(BaseModel):
    decision: Literal["通过", "补充资料", "拒绝"]
    risk_level: str
    comment: str
    operator: str = "reviewer-001"


@app.get("/api/health")
def health(): 
    return {"status": "ok"}


@app.get("/api/applications")
def list_applications():
    return enrich_applications(load_applications())


@app.post("/api/applications/assess")
def assess_application(application: LoanApplication):
    if application.down_payment > application.vehicle_price:
        raise HTTPException(status_code=422, detail="首付金额不能超过车辆价格")
    if application.loan_amount + application.down_payment > application.vehicle_price * 1.05:
        raise HTTPException(status_code=422, detail="贷款与首付总额明显超过车辆价格")
        
        items = load_applications()
        
        record = {
        "id": f"CL-{uuid4().hex[:10].upper()}",
        **application.model_dump(),
        "status": "待风险评估",
        "created_at": datetime.now().isoformat(),
    }
        
        items.append(record)
        save_applications(items)
        
        return record


@app.post("/api/applications/{app_id}/assess")
def assess_application(app_id: str):
    items, index, application = find_application(app_id)
    result = assess(application)

    assessment_record = {
        "application_id": app_id,
        **result,
        "assessed_at": datetime.now().isoformat(),
    }
    assessments = load_assessments()
    assessments.append(assessment_record)
    save_assessments(assessments)

    items[index]["status"] = "待人工复核"
    save_applications(items)

    return {"application": items[index], "assessment": result}


@app.post("/api/applications/{application_id}/decision")
def save_decision(application_id: str, decision: Decision):
    items = load_applications()

    for item in items:
        if item.get("id") == application_id:
            if item.get("status") not in {"待人工复核", "补充资料"}:
                raise HTTPException(status_code=409, detail="当前案件状态不允许重复审批")

            item["status"] = decision.decision
            item["decision"] = decision.model_dump()
            save_applications(items)

            logs = load_audit_logs()
            logs.append({
                "id": uuid4().hex,
                "application_id": application_id,
                "action": "人工复核",
                "decision": decision.decision,
                "risk_level": decision.risk_level,
                "comment": decision.comment,
                "operator": decision.operator,
                "created_at": datetime.now().isoformat(),
            })
            save_audit_logs(logs)
            return enrich_applications([item])[0]

    raise HTTPException(status_code=404, detail="案件不存在")


@app.get("/api/applications/{application_id}/audit")
def get_audit_logs(application_id: str):
    find_application(application_id)
    return [
        log for log in load_audit_logs()
        if log.get("application_id") == application_id
    ]


app.mount(
    "/",
    StaticFiles(directory=ROOT / "frontend", html=True),
    name="frontend",
)
