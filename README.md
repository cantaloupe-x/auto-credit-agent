# Auto Credit Agent

汽车贷款 AI 信贷审批与风控 Agent，第一版打通申请资料、案件队列、规则评估、风险解释和人工复核展示。

## 当前范围

- 已完成：前端审批工作台、申请人入口、固定模拟案件、确定性风险规则、FastAPI 接口骨架、测试样例。
- 部分完成：前端当前仍使用内置模拟数据，尚未完成前后端联调与数据库持久化。
- 尚未完成：真实征信接口、登录权限、生产级部署、放款还款流程。

## 启动

```bash
pip install -r backend/requirements.txt
uvicorn backend.app:app --reload
```

前端可直接打开 `frontend/index.html`。API 文档位于 `/docs`。

## 四人协作建议

前端、后端、风控 Agent、测试与交付分别从 feature 分支开发，通过 Pull Request 合并到 main。
