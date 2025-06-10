from fastapi import FastAPI
from app.profile.api import router as user_router
from app.profiles.farmer.api import router as farmer_router
from app.wholesale_company.company.api import router as company_router
from app.wholesale_company.center.api import router as center_router
from app.profiles.wholesaler.api import router as wholesaler_router
from app.profiles.retailer.api import router as retailer_router
from app.transactions.wholesale_contract.api import router as wholesale_contract_router
from app.transactions.wholesale_shipment.api import router as wholesale_shipment_router
from app.transactions.retail_contract.api import router as retail_contract_router
from app.transactions.retail_shipment.api import router as retail_shipment_router
from app.core.auth.api import router as auth_router
from app.wholesale_company.inventory.api import router as inventory_router
from app.wholesale_company.management.api import router as managemet_router

app = FastAPI()


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(farmer_router)
app.include_router(company_router)
app.include_router(center_router)
app.include_router(wholesaler_router)
app.include_router(retailer_router)
app.include_router(wholesale_contract_router)
app.include_router(wholesale_shipment_router)
app.include_router(retail_contract_router)
app.include_router(retail_shipment_router)
app.include_router(inventory_router)
app.include_router(managemet_router)

@app.get("/")
def root():
    return {"message": "HADALA API 서버가 실행 중입니다."} 