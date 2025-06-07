from fastapi import FastAPI
from app.user.api import router as user_router
from app.farmer.api import router as farmer_router
from app.company.api import router as company_router
from app.center.api import router as center_router
from app.wholesaler.api import router as wholesaler_router
from app.core.auth.api import router as auth_router
from app.retailer.api import router as retailer_router

app = FastAPI()

app.include_router(user_router)
app.include_router(farmer_router)
app.include_router(company_router)
app.include_router(center_router)
app.include_router(wholesaler_router)
app.include_router(auth_router)
app.include_router(retailer_router)

@app.get("/")
def root():
    return {"message": "HADALA API 서버가 실행 중입니다."} 