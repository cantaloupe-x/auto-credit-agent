# Auto Credit Agent

汽车贷款 AI 信贷审批与风控 Agent，第一版打通申请资料、案件队列、规则评估、版本化知识检索、风险解释、补件建议和人工复核展示。仓库内所有人物、案件、金额、知识与评测记录均为完全虚构的测试数据。

## 当前范围

- 已完成：前端审批工作台、申请人入口、固定可复现模拟案件、确定性风险规则、版本化本地知识库、无模型 Key 的 Agent 工作流、结构化 API 与自动化评测。
- 部分完成：前端当前仍使用内置模拟数据，尚未完成前后端联调与数据库持久化。
- 尚未完成：真实征信接口、登录权限、生产级部署、放款还款流程。

## 启动

```bash
pip install -r backend/requirements.txt
uvicorn backend.app:app --reload
```

前端可直接打开 `frontend/index.html`。API 文档位于 `/docs`。

Agent 的职责边界是检索依据、解释风险和提出补件建议；`backend/risk_engine.py` 中的规则是唯一评分来源。任何建议都保持 `pending`，最终决定必须由人工确认。字段、状态和版本集中在 `backend/domain.py`，API Schema 位于 `backend/schemas.py`。

```bash
pytest -q
```

详细的数据字典与接口约定见 `docs/data-dictionary.md` 和 `docs/agent-api.md`。

## 四人协作建议

前端、后端、风控 Agent、测试与交付分别从 feature 分支开发，通过 Pull Request 合并到 main。
