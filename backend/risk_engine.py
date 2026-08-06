"""Deterministic first-version auto-loan risk rules."""

def assess(app):
    income = float(app.get("income", 0))
    debt = float(app.get("monthly_debt", 0))
    score = 100
    reasons = []
    if income <= 0:
        return {"score": 0, "level": "高风险", "recommendation": "补充收入资料", "reasons": ["收入缺失或无效"], "model_version": "rule-v1.0"}
    dti = debt / income
    if dti > .5: score -= 25; reasons.append(f"负债收入比 {dti:.1%}，超过 50%")
    elif dti > .4: score -= 12; reasons.append(f"负债收入比 {dti:.1%}")
    if float(app.get("down_payment", 0)) / max(float(app.get("vehicle_price", 1)), 1) < .2:
        score -= 15; reasons.append("首付比例低于 20%")
    if float(app.get("work_years", 0)) < 1:
        score -= 10; reasons.append("当前任职时间不足 1 年")
    if app.get("recent_overdue", False):
        score -= 15; reasons.append("近 6 个月存在逾期记录")
    if not reasons: reasons.append("收入、负债和首付比例处于合理区间")
    score = max(0, score)
    level = "低风险" if score >= 80 else "中低风险" if score >= 60 else "中风险" if score >= 40 else "高风险"
    recommendation = "建议通过" if score >= 80 else "建议人工确认" if score >= 60 else "建议补充资料" if score >= 40 else "建议谨慎处理"
    return {"score": score, "level": level, "recommendation": recommendation, "reasons": reasons, "model_version": "rule-v1.0"}
