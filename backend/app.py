from pathlib import Path
import json
from fastapi import FastAPI, HTTPException
from .agent import run_agent
from .domain import DEFAULT_KNOWLEDGE_VERSION, SCHEMA_VERSION, WORKFLOW_VERSION
from .risk_engine import assess
from .schemas import AgentRequest, AgentResponse, LoanApplication

app = FastAPI(title="Auto Credit Agent API")
DATA = Path(__file__).parents[1] / "data" / "applicants.json"

def _dump_model(model):
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()

@app.get("/api/health")
def health(): return {"status": "ok"}

@app.get("/api/applications")
def list_applications():
    return json.loads(DATA.read_text(encoding="utf-8"))

@app.post("/api/applications/assess")
def assess_application(application: LoanApplication):
    payload = _dump_model(application)
    result = assess(payload)
    return {"application": payload, "assessment": result}

@app.get("/api/agent/metadata")
def agent_metadata():
    return {"schema_version": SCHEMA_VERSION, "workflow_version": WORKFLOW_VERSION, "default_knowledge_version": DEFAULT_KNOWLEDGE_VERSION, "model_api_required": False, "final_decision": "human_confirmation_required", "fictional_test_data": True}

@app.post("/api/agent/evaluate", response_model=AgentResponse)
def evaluate_with_agent(request: AgentRequest):
    try:
        return run_agent(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
