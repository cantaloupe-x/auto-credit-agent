# Auto Credit Agent

汽车贷款 AI 信贷审批与风控 Agent。当前已打通申请资料、规则评估、案件保存、人工复核和审计记录，并完成前后端联调。

## 当前范围

- 已完成：申请入口、审批工作台、确定性风险规则、SQLite 持久化、人工复核、审计记录、版本化本地知识库、无模型 Key 的 Agent 工作流和自动化测试。
- 尚未完成：真实征信接口、登录权限、生产级部署、放款还款流程。

## 启动后端

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --reload
```

打开 `http://127.0.0.1:8000` 使用完整网页；打开 `http://127.0.0.1:8000/docs` 可以直接测试 API。首次启动会创建 `data/auto_credit.db`，并导入 `data/applicants.json` 中的两条模拟案件。

## 核心 API

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| `GET` | `/api/health` | 检查服务状态 |
| `GET` | `/api/applications` | 查看案件队列 |
| `POST` | `/api/applications` | 提交、评估并保存申请 |
| `POST` | `/api/applications/assess` | 仅运行风险评估，不保存 |
| `GET` | `/api/applications/{id}` | 查看单个案件 |
| `PATCH` | `/api/applications/{id}/review` | 保存人工复核结论 |
| `GET` | `/api/applications/{id}/audit` | 查看案件审计记录 |

人工复核的 `decision` 支持 `approved`、`needs_more_info` 和 `rejected`。模型只提供建议，最终结论由审批人员确认。

## 运行测试

```bash
pip install -r backend/requirements-dev.txt
python -m pytest -q
```

测试覆盖网页入口、风险等级、缺失或无效输入、案件持久化、人工复核、审计记录和接口失败场景。

## 前端

网页由 FastAPI 同源提供，不要直接双击 `frontend/index.html`。案件队列、申请提交、风险结果、人工复核、审计记录、搜索、筛选和导出都已接入真实运行逻辑；征信、收入流水和身份核验仍是模拟边界。

## 版本化知识库与 Agent 接口

知识库位于 `knowledge/risk-knowledge-v1.0/knowledge.json`，包含 11 条版本化测试知识，覆盖 DTI、首付、任职、逾期、融资金额一致性、贷款期限、资料完整度、收入核验、重复申请、授权范围和人工确认。`backend/knowledge.py` 负责本地确定性检索。

`backend/risk_engine.py` 是唯一的评分来源；Agent 只基于检索结果解释风险和建议补件，不能修改评分、自动批准或自动拒绝，最终决定必须由人工确认。

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| `GET` | `/api/agent/metadata` | 查看 schema / workflow / 知识版本 |
| `POST` | `/api/agent/evaluate` | 生成带引用和补件建议的结构化结果 |

字段、状态和版本集中在 `backend/domain.py`，API Schema 位于 `backend/schemas.py`。详细约定见 `docs/data-dictionary.md` 和 `docs/agent-api.md`。

## 数据说明

- `data/applicants.json`：2 条带完整展示字段的模拟案件，服务首次启动时导入数据库，作为审批队列的初始数据。
- `data/agent_eval_cases.json`：15 个 Agent 评测案例，覆盖风险等级、规则边界、缺件、无效输入和知识版本异常。

以上人物、案件、金额和记录全部为虚构测试数据，不对应任何真实个人或授信业务。
