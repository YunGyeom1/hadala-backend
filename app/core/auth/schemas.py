from pydantic import BaseModel
from typing import Optional


class GoogleOAuthLoginRequest(BaseModel):
    id_token: str

class GoogleOAuthLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class VerifyRefreshTokenRequest(BaseModel):
    refresh_token: str

class VerifyRefreshTokenResponse(BaseModel):
    valid: bool
    error: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


