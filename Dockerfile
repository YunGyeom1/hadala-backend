FROM python:3.10-slim

WORKDIR /app

# 백엔드 코드 복사
COPY ./ /app

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]