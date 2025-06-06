from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class WholesalerBase(BaseModel):
    name: str
    role: Optional[str] = None
    phone: Optional[str] = None

class WholesalerCreate(WholesalerBase):
    user_id: UUID4
    company_id: UUID4

class WholesalerUpdate(WholesalerBase):
    name: Optional[str] = None

class WholesalerInDB(WholesalerBase):
    id: UUID4
    user_id: UUID4
    company_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WholesalerResponse(WholesalerInDB):
    pass

class WholesalerRoleUpdate(BaseModel):
    role: str

class WholesalerOwnerUpdate(BaseModel):
    new_owner_id: UUID4