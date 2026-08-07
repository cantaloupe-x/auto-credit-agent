"""Deterministic first-version auto-loan risk rules."""


def assess(app):
    income = float(app.get("income", 0))
    debt = float(app.get("monthly_debt", 0))
    vehicle_price = float(app.get("vehicle_price", 0))
    down_payment = float(app.get("down_payment", 0))
    work_years = float(app.get("work_years", 0))

    if debt < 0 or down_payment < 0 or work_years < 0:
        raise ValueError("金额和任职年限不能为负数")
    if vehicle_price <= 0:
        raise ValueError("车辆价格必须大于 0")
    if income <= 0:
        return {
            "score": 0,
            "level": "高风险",
            "recommendation": "补充收入资料",
            "reasons": ["收入缺失或无效"],
            "model_version": "rule-v1.0",
        }

    score = 100
    reasons = []
    debt_to_income = debt / income
    if debt_to_income > 0.5:
        score -= 25
        reasons.append(f"负债收入比 {debt_to_income:.1%}，超过 50%")
    elif debt_to_income > 0.4:
        score -= 12
        reasons.append(f"负债收入比 {debt_to_income:.1%}")

    if down_payment / vehicle_price < 0.2:
        score -= 15
        reasons.append("首付比例低于 20%")
    if work_years < 1:
        score -= 10
        reasons.append("当前任职时间不足 1 年")
    if app.get("recent_overdue", False):
        score -= 15
        reasons.append("近 6 个月存在逾期记录")
    if not reasons:
        reasons.append("收入、负债和首付比例处于合理区间")

    score = max(0, score)
    if score >= 80:
        level, recommendation = "低风险", "建议通过"
    elif score >= 60:
        level, recommendation = "中低风险", "建议人工确认"
    elif score >= 40:
        level, recommendation = "中风险", "建议补充资料"
    else:
        level, recommendation = "高风险", "建议谨慎处理"

    return {
        "score": score,
        "level": level,
        "recommendation": recommendation,
        "reasons": reasons,
        "model_version": "rule-v1.0",
    }
