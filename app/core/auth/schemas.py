from pydantic import BaseModel
from typing import Optional

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: Optional[str] = None

class VerifyTokenRequest(BaseModel):
    access_token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class GoogleOAuthLoginRequest(BaseModel):
    id_token: str

class GoogleOAuthLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str

class VerifyTokenResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    error: Optional[str] = None 