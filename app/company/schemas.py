from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class CompanyBase(BaseModel):
    name: str
    description: Optional[str] = None
    business_number: str
    address: str
    phone: str
    email: EmailStr


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class CompanyOut(CompanyBase):
    id: UUID
    owner: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyList(BaseModel):
    items: List[CompanyOut]
    total: int
    skip: int
    limit: int


class WholesalerOut(BaseModel):
    id: UUID
    user_id: UUID
    role: str
    company_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 