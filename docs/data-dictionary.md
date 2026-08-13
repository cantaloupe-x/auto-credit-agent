# 数据字典

版本：`agent-schema-v1.0`。本文和仓库内全部样例均为完全虚构的测试数据，不对应真实个人、车辆或授信业务。字段和状态的可执行定义集中在 `backend/domain.py`。

## 申请字段

| 字段 | 类型 | 单位/含义 | 必填 |
|---|---|---|---|
| name | string | 虚构测试申请人姓名 | 是 |
| income | number | 月均收入，人民币元，必须大于 0 | 是 |
| monthly_debt | number | 每月存量债务支出，人民币元，不得为负 | 是 |
| vehicle_price | number | 车辆价格，人民币元，必须大于 0 | 是 |
| down_payment | number | 首付金额，人民币元，不得为负 | 是 |
| loan_amount | number | 申请贷款金额，人民币元，不得为负 | 是 |
| loan_term | integer | 期数（月），允许 6 至 84，默认 36 | 否 |
| work_years | number | 当前单位任职年限，不得为负，默认 3 | 否 |
| recent_overdue | boolean | 近六个月是否有虚构逾期记录 | 否 |

## 状态和职责

- 申请状态：`received`、`assessed`、`pending_human_review`、`completed`。
- 人工决定：`pending`、`approved`、`more_information_required`、`declined`。
- Agent 永远只输出 `pending`；只有外部人工复核流程可写入其余决定。
- 规则引擎独占 `score`、`level`、`recommendation` 和 `reasons` 的计算。
- 知识库条目必须带固定 ID、版本、依据文本和资料要求。

## 固定数据资产

- `data/applicants.json`：产品演示案件，`fictional-auto-loan-v1.1`。
- `data/agent_eval_cases.json`：Agent 回归评测，`agent-eval-fictional-v1.1`。
- `knowledge/risk-knowledge-v1.0/knowledge.json`：虚构测试知识，版本不可原地改语义；有实质修改应新增版本目录。
