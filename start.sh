#!/bin/bash

# 데이터베이스 마이그레이션 실행
echo "Running database migrations..."
alembic upgrade head

# 애플리케이션 시작
echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT 