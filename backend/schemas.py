"""Agent API 的版本化结构化输入输出。"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .domain import AgentMode, HumanDecision, SCHEMA_VERSION


class LoanApplication(BaseModel):
    name: str = Field(..., description="虚构测试申请人姓名")
    income: float = Field(gt=0)
    monthly_debt: float = Field(ge=0)
    vehicle_price: float = Field(gt=0)
    down_payment: float = Field(ge=0)
    loan_amount: float = Field(ge=0)
    loan_term: int = Field(default=36, ge=6, le=84)
    work_years: float = Field(default=3, ge=0)
    recent_overdue: bool = False

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("姓名不能为空")
        return value


class AgentRequest(BaseModel):
    application: LoanApplication
    missing_documents: List[str] = Field(default_factory=list)
    knowledge_version: Optional[str] = None
    trace_id: Optional[str] = None


class KnowledgeCitation(BaseModel):
    knowledge_id: str
    title: str
    version: str
    excerpt: str


class AgentResponse(BaseModel):
    schema_version: str = SCHEMA_VERSION
    trace_id: str
    mode: AgentMode = AgentMode.DETERMINISTIC
    rule_assessment: Dict[str, object]
    risk_explanation: str
    citations: List[KnowledgeCitation]
    requested_documents: List[str]
    next_action: str = "提交人工复核"
    human_decision: HumanDecision = HumanDecision.PENDING
    disclaimer: str = "完全虚构的测试输出；Agent 仅提供依据、解释和补件建议，最终决定必须由人工确认。"
