from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TokenPayload(BaseModel):
    sub: str  # User ID
    token_type: str
    exp: datetime

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class VerifyTokenRequest(BaseModel):
    access_token: str

class VerifyTokenResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    error: Optional[str] = None

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

class GoogleUserInfo(BaseModel):
    email: str
    name: str
    sub: str  # Google OAuth 고유 ID
    picture: str