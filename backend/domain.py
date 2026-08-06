"""集中定义产品字段、状态和版本，便于后续页面方案统一调整。"""

from enum import Enum


DATASET_VERSION = "fictional-auto-loan-v1.1"
SCHEMA_VERSION = "agent-schema-v1.0"
WORKFLOW_VERSION = "agent-workflow-v1.0"
PROMPT_VERSION = "agent-prompt-v1.0"
DEFAULT_KNOWLEDGE_VERSION = "risk-knowledge-v1.0"
RULE_MODEL_VERSION = "rule-v1.0"


class ApplicationStatus(str, Enum):
    RECEIVED = "received"
    ASSESSED = "assessed"
    PENDING_HUMAN_REVIEW = "pending_human_review"
    COMPLETED = "completed"


class HumanDecision(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    MORE_INFORMATION = "more_information_required"
    DECLINED = "declined"


class RiskLevel(str, Enum):
    LOW = "低风险"
    MEDIUM_LOW = "中低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"


class AgentMode(str, Enum):
    DETERMINISTIC = "deterministic"


APPLICATION_FIELD_DEFINITIONS = {
    "name": "虚构申请人姓名，仅用于测试",
    "income": "月均收入，人民币元",
    "monthly_debt": "现有每月债务支出，人民币元",
    "vehicle_price": "车辆价格，人民币元",
    "down_payment": "首付金额，人民币元",
    "loan_amount": "申请贷款金额，人民币元",
    "loan_term": "贷款期数，月；允许 6 至 84 个月",
    "work_years": "当前单位任职年限",
    "recent_overdue": "近六个月是否存在逾期测试记录",
}
