from dataclasses import dataclass, asdict

@dataclass
class Application:
    name: str
    income: float
    monthly_debt: float
    vehicle_price: float
    down_payment: float
    loan_amount: float
    loan_term: int = 36
    work_years: float = 3
    recent_overdue: bool = False

    def to_dict(self):
        return asdict(self)
