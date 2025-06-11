from fastapi import FastAPI

app = FastAPI()

from app.company.manage.api import router as manage_router

app.include_router(manage_router)

@app.get("/")
def root():
    return {"message": "HADALA API 서버가 실행 중입니다."} 