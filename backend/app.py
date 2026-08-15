from pathlib import Path
import json

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .risk_engine import assess

ROOT = Path(__file__).parents[1]
DATA = ROOT / "data" / "applicants.json"

app = FastAPI(title="Auto Credit Agent API")

class LoanApplication(BaseModel):
    name: str
    income: float
    monthly_debt: float
    vehicle_price: float
    down_payment: float
    loan_amount: float
    loan_term: int = 36
    work_years: float = 3
    recent_overdue: bool = False

@app.get("/api/health")
def health(): return {"status": "ok"}

@app.get("/api/applications")
def list_applications():
    return json.loads(DATA.read_text(encoding="utf-8"))

@app.post("/api/applications/assess")
def assess_application(application: LoanApplication):
    result = assess(application.model_dump())
    return {"application": application.model_dump(), "assessment": result}

app.mount(
    "/",
    StaticFiles(directory=ROOT / "frontend", html=True),
    name="frontend",
)
