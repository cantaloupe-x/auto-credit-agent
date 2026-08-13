FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . .

# 持久磁盘挂到 /var/data，数据库文件放在里面，这样重启和重新部署都不会丢案件。
ENV AUTO_CREDIT_DB=/var/data/auto_credit.db
ENV PORT=8000
EXPOSE 8000

# 平台会注入 PORT，用 sh -c 才能让变量展开。
CMD ["sh", "-c", "mkdir -p \"$(dirname \"$AUTO_CREDIT_DB\")\" && python -m uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
