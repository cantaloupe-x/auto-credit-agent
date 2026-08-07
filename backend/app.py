from contextlib import asynccontextmanager
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse

from .models import LoanApplication, ReviewRequest
from .risk_engine import assess
from .storage import ApplicationStore


ROOT = Path(__file__).parents[1]
DEFAULT_DATABASE = ROOT / "data" / "auto_credit.db"
SEED_DATA = ROOT / "data" / "applicants.json"


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

    @api.post("/api/applications/assess")
    def assess_application(application: LoanApplication):
        payload = application.model_dump()
        return {"application": payload, "assessment": assess(payload)}

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
