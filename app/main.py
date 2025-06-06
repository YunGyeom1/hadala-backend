from fastapi import FastAPI
from app.user.api import router as user_router
from app.farmer.api import router as farmer_router
from app.company.api import router as company_router
from app.center.api import router as center_router
from app.wholesaler.api import router as wholesaler_router
from app.core.auth.api import router as auth_router

app = FastAPI()

app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(farmer_router, prefix="/farmers", tags=["farmers"])
app.include_router(company_router, prefix="/companies", tags=["companies"])
app.include_router(center_router, prefix="/centers", tags=["centers"])
app.include_router(wholesaler_router, prefix="/wholesalers", tags=["wholesalers"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
def root():
    return {"message": "HADALA API 서버가 실행 중입니다."} 