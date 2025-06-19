from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "HADALA API 서버가 실행 중입니다."} 