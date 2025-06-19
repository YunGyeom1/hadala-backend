from fastapi import FastAPI
from app.core.auth.api import router as auth_router
from app.company.common.api import router as common_router
from app.company.detail.wholesale.api import router as wholesale_router
# from app.company.detail.retail.api import router as retail_router
# from app.company.detail.farmer.api import router as farmer_router
from app.company.inventory_snapshot.api import router as inventory_snapshot_router
from app.company.center.api import router as center_router
from app.transactions.shipment.api import router as shipment_router
from app.transactions.contract.api import router as contract_router
from app.transactions.summary.api import router as summary_router
from app.profile.api import router as profile_router


app = FastAPI()

app.include_router(auth_router)
app.include_router(common_router)
app.include_router(wholesale_router)
# app.include_router(retail_router)
# app.include_router(farmer_router)
app.include_router(inventory_snapshot_router)
app.include_router(center_router)
app.include_router(shipment_router)
app.include_router(contract_router)
app.include_router(summary_router)
app.include_router(profile_router)

@app.get("/")
def root():
    return {"message": "HADALA API 서버가 실행 중입니다."} 