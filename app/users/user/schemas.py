from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
from uuid import UUID


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    picture_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    picture_url: Optional[HttpUrl] = None
