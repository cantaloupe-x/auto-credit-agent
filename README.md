# Auto Credit Agent

汽车贷款 AI 信贷审批与风控 Agent，第一版打通申请资料、案件队列、规则评估、版本化知识检索、风险解释、补件建议和人工复核展示。仓库内所有人物、案件、金额、知识与评测记录均为完全虚构的测试数据。

## 当前范围

- 已完成：前端审批工作台、申请人入口、固定可复现模拟案件、确定性风险规则、版本化本地知识库、无模型 Key 的 Agent 工作流、结构化 API 与自动化评测。
- 部分完成：前端当前仍使用内置模拟数据，尚未完成前后端联调与数据库持久化。
- 尚未完成：真实征信接口、登录权限、生产级部署、放款还款流程。

## 启动

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --reload
```

前端可直接打开 `frontend/index.html`。API 文档位于 `/docs`。

## 数据与评测

- `data/applicants.json` 包含 15 条固定、可复现的虚构汽车贷款申请数据，覆盖不同风险情况。
- `data/agent_eval_cases.json` 包含 15 个代表性 Agent 评测案例，覆盖风险等级、规则边界、缺件、无效输入和知识版本异常等场景。

上述数据中的人物、案件、金额和记录全部为虚构测试数据，不对应任何真实个人或授信业务。

## 版本化知识库

当前知识库位于 `knowledge/risk-knowledge-v1.0/knowledge.json`，包含 11 条版本化测试知识，覆盖 DTI、首付、任职、逾期、融资金额一致性、贷款期限、资料完整度、收入核验、重复或异常申请、授权范围和人工确认。

`backend/knowledge.py` 负责本地确定性检索。`backend/risk_engine.py` 中的规则是唯一评分来源；Agent 只能基于检索结果解释风险和建议补件，不能修改评分、自动批准或自动拒绝，最终决定必须由人工确认。

## Agent API

- `GET /api/agent/metadata`
- `POST /api/agent/evaluate`

字段、状态和版本集中在 `backend/domain.py`，API Schema 位于 `backend/schemas.py`。详细的数据字典与接口约定见 `docs/data-dictionary.md` 和 `docs/agent-api.md`。

## 测试

```bash
python -m pytest -q
```

## 四人协作建议

前端、后端、风控 Agent、测试与交付分别从 feature 分支开发，通过 Pull Request 合并到 main。
