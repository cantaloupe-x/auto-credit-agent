from typing import Literal

from pydantic import BaseModel, Field, model_validator


class LoanApplication(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    id_number: str | None = Field(default=None, max_length=32)
    city: str | None = Field(default=None, max_length=80)
    occupation: str | None = Field(default=None, max_length=80)
    vehicle_model: str | None = Field(default=None, max_length=120)
    vehicle_source: str | None = Field(default=None, max_length=80)
    income: float = Field(ge=0)
    monthly_debt: float = Field(ge=0)
    vehicle_price: float = Field(gt=0)
    down_payment: float = Field(ge=0)
    loan_amount: float = Field(gt=0)
    loan_term: Literal[24, 36, 48] = 36
    work_years: float = Field(default=3, ge=0)
    recent_overdue: bool = False
    authorized: bool

    @model_validator(mode="after")
    def validate_financing(self):
        if not self.authorized:
            raise ValueError("必须确认资料使用授权")
        if self.down_payment > self.vehicle_price:
            raise ValueError("首付金额不能高于车辆价格")
        if self.loan_amount + self.down_payment > self.vehicle_price:
            raise ValueError("贷款金额与首付之和不能高于车辆价格")
        return self


class ReviewRequest(BaseModel):
    decision: Literal["approved", "needs_more_info", "rejected"]
    comment: str = Field(min_length=1, max_length=1000)
    reviewer: str = Field(default="审批员", min_length=1, max_length=80)
