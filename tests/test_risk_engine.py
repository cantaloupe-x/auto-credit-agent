import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from risk_engine import assess

def test_low_risk_case():
    result = assess({"income": 20000, "monthly_debt": 3000, "vehicle_price": 200000, "down_payment": 80000, "work_years": 5})
    assert result["score"] >= 80

def test_high_debt_case():
    result = assess({"income": 20000, "monthly_debt": 14000, "vehicle_price": 300000, "down_payment": 40000, "work_years": .5, "recent_overdue": True})
    assert result["score"] < 60
