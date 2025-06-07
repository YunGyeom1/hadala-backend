from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class WholesalerBase(BaseModel):
    name: str
    address: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class WholesalerCreate(WholesalerBase):
    pass

class WholesalerUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class WholesalerOut(WholesalerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WholesalerResponse(WholesalerOut):
    pass

class WholesalerRoleUpdate(BaseModel):
    role: str

class WholesalerOwnerUpdate(BaseModel):
    new_owner_id: UUID