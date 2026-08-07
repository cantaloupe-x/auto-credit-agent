# Auto Credit Agent

汽车贷款 AI 信贷审批与风控 Agent。当前已打通申请资料、规则评估、案件保存、人工复核和审计记录，并完成前后端联调。

## 当前范围

- 已完成：申请入口、审批工作台、确定性风险规则、SQLite 持久化、人工复核、审计记录和自动化测试。
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
