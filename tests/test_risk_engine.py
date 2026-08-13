import pytest

from backend.risk_engine import assess


def test_low_risk_case():
    result = assess(
        {
            "income": 20000,
            "monthly_debt": 3000,
            "vehicle_price": 200000,
            "down_payment": 80000,
            "work_years": 5,
        }
    )

    assert result["score"] == 100
    assert result["level"] == "低风险"


def test_high_risk_case():
    result = assess(
        {
            "income": 20000,
            "monthly_debt": 14000,
            "vehicle_price": 300000,
            "down_payment": 40000,
            "work_years": 0.5,
            "recent_overdue": True,
        }
    )

    assert result["score"] == 35
    assert result["level"] == "高风险"


def test_missing_income_requires_more_information():
    result = assess(
        {
            "income": 0,
            "monthly_debt": 0,
            "vehicle_price": 200000,
            "down_payment": 50000,
            "work_years": 3,
        }
    )

    assert result["score"] == 0
    assert result["recommendation"] == "补充收入资料"


def test_negative_debt_is_rejected():
    with pytest.raises(ValueError, match="不能为负数"):
        assess(
            {
                "income": 20000,
                "monthly_debt": -1,
                "vehicle_price": 200000,
                "down_payment": 50000,
                "work_years": 3,
            }
        )
