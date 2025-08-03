from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.auth.api import router as auth_router
from app.company.common.api import router as common_router
from app.company.center.api import router as center_router
from app.company.inventory_snapshot.api import router as inventory_snapshot_router
from app.company.detail.wholesale.api import router as wholesale_router
from app.company.detail.retail.api import router as retail_router
from app.company.detail.farmer.api import router as farmer_router
from app.transactions.shipment.api import router as shipment_router
from app.transactions.contract.api import router as contract_router
from app.transactions.summary.api import router as summary_router
from app.transactions.payment.api import router as payment_router
from app.profile.api import router as profile_router
import os

app = FastAPI()

class SetCOOPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cross-Origin-Opener-Policy"] = "unsafe-none"
        return response

app.add_middleware(SetCOOPMiddleware)

app.include_router(auth_router)
app.include_router(common_router)
app.include_router(wholesale_router)
app.include_router(retail_router)
app.include_router(farmer_router)
app.include_router(inventory_snapshot_router)
app.include_router(center_router)
app.include_router(shipment_router)
app.include_router(contract_router)
app.include_router(summary_router)
app.include_router(payment_router)
app.include_router(profile_router)

# 배포 환경에 따른 CORS 설정
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://hadala-frontend-production.up.railway.app",  # Vercel 배포 시
    
    "https://hadala-frontend.onrender.com",  # Render 배포 시
]

# 환경 변수에서 추가 origin 가져오기
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))



app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "HADALA API 서버가 실행 중입니다."} 