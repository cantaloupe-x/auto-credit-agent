from contextlib import asynccontextmanager
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse

from .agent import run_agent
from .domain import DEFAULT_KNOWLEDGE_VERSION, SCHEMA_VERSION, WORKFLOW_VERSION
from .models import LoanApplication, ReviewRequest
from .risk_engine import assess
from .schemas import AgentRequest, AgentResponse
from .schemas import LoanApplication as AgentLoanApplication
from .storage import ApplicationStore


ROOT = Path(__file__).parents[1]
SEED_DATA = ROOT / "data" / "applicants.json"

# 部署时用 AUTO_CREDIT_DB 指向持久磁盘的挂载目录，例如 /var/data/auto_credit.db。
# 不设这个变量就还是走仓库里的 data/auto_credit.db，本地开发不受影响。
DEFAULT_DATABASE = Path(os.environ.get("AUTO_CREDIT_DB") or ROOT / "data" / "auto_credit.db")


def create_app(database_path=None):
    store = ApplicationStore(database_path or DEFAULT_DATABASE)

    @asynccontextmanager
    async def lifespan(_app):
        store.initialize()
        if store.is_empty():
            seed_applications(store)
        yield

    api = FastAPI(title="Auto Credit Agent API", lifespan=lifespan)

    @api.get("/", include_in_schema=False)
    def frontend():
        return FileResponse(ROOT / "frontend" / "index.html")

    @api.get("/api/health")
    def health():
        return {"status": "ok", "database": "ok"}

    @api.get("/api/applications")
    def list_applications():
        return store.list_applications()

    @api.get("/api/applications/{application_id}")
    def get_application(application_id: str):
        application = store.get_application(application_id)
        if application is None:
            raise HTTPException(status_code=404, detail="案件不存在")
        return application

    # 只评估不落库：沿用 PR #1 的宽松输入模型，允许不带前端展示字段的最小载荷。
    @api.post("/api/applications/assess")
    def assess_application(application: AgentLoanApplication):
        payload = application.model_dump()
        return {"application": payload, "assessment": assess(payload)}

    # 落库的申请必须带齐前端字段和资料使用授权，用严格模型。
    @api.post("/api/applications", status_code=status.HTTP_201_CREATED)
    def create_application(application: LoanApplication):
        payload = application.model_dump()
        return store.create_application(payload, assess(payload))

    @api.patch("/api/applications/{application_id}/review")
    def review_application(application_id: str, review: ReviewRequest):
        application = store.review_application(application_id, **review.model_dump())
        if application is None:
            raise HTTPException(status_code=404, detail="案件不存在")
        return application

    @api.get("/api/applications/{application_id}/audit")
    def list_audit_events(application_id: str):
        events = store.list_audit_events(application_id)
        if events is None:
            raise HTTPException(status_code=404, detail="案件不存在")
        return events

    # 以下两个端点来自 PR #1 的知识与评估工作流。
    @api.get("/api/agent/metadata")
    def agent_metadata():
        return {
            "schema_version": SCHEMA_VERSION,
            "workflow_version": WORKFLOW_VERSION,
            "default_knowledge_version": DEFAULT_KNOWLEDGE_VERSION,
            "model_api_required": False,
            "final_decision": "human_confirmation_required",
            "fictional_test_data": True,
        }

    @api.post("/api/agent/evaluate", response_model=AgentResponse)
    def evaluate_with_agent(request: AgentRequest):
        try:
            return run_agent(request)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    return api


def seed_applications(store):
    records = json.loads(SEED_DATA.read_text(encoding="utf-8"))
    for record in records:
        application_id = record.pop("id")
        record["authorized"] = True
        application = LoanApplication(**record)
        payload = application.model_dump()
        store.create_application(
            payload,
            assess(payload),
            application_id=application_id,
            actor="系统导入",
        )


app = create_app()
