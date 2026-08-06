# Agent API

所有接口仅处理完全虚构的测试数据。现有 FastAPI 风险接口保持兼容；Agent 不需要模型 API Key，也不读取网络或环境变量。

## `POST /api/applications/assess`

兼容接口。接收申请字段，返回原有 `application` 和 `assessment`；评分仅由 `rule-v1.0` 产生。

## `POST /api/agent/evaluate`

请求：

```json
{"application":{"name":"测试申请人","income":20000,"monthly_debt":3000,"vehicle_price":200000,"down_payment":80000,"loan_amount":120000},"missing_documents":[],"knowledge_version":"risk-knowledge-v1.0","trace_id":"optional-client-trace"}
```

响应包含 `schema_version`、确定性 `trace_id`、`mode`、不可变的 `rule_assessment`、`risk_explanation`、带版本的 `citations`、去重后的 `requested_documents`、`next_action`、`human_decision` 和免责声明。`human_decision` 固定为 `pending`，`next_action` 固定要求人工复核。

未知知识版本返回 HTTP 422。相同输入、规则版本和知识版本会得到相同输出。

基础输入校验包括：姓名去除首尾空格后不得为空，收入和车价必须大于零，其他金额及工作年限不得为负，贷款期限必须为 6 至 84 个月。校验失败返回 HTTP 422。首付与贷款金额之和同车辆价格的差异超过车辆价格 1% 或 1,000 元（取较大值）时，由规则产生风险提示并扣 10 分，Agent 检索金额一致性依据，但仍只提交人工确认。

## `GET /api/agent/metadata`

返回当前 Schema、工作流和默认知识版本，并明确 `model_api_required=false`、`final_decision=human_confirmation_required` 和 `fictional_test_data=true`。

## 工作流与 Guardrails

1. 固定规则评分；Agent 不得修改。
2. 根据规则原因和显式缺件从指定版本本地知识库检索。
3. 仅引用检索结果生成确定性解释与补件清单。
4. 不声称已调用外部征信或完成核验，不自动通过或拒绝。
5. 输出交给人工确认并在业务系统留痕。

Prompt 和 guardrails 的集中定义见 `backend/prompts.py`，工作流版本为 `agent-workflow-v1.0`。
