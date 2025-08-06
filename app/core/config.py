from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    # JWT 설정
    SECRET_KEY: str = "your-secret-key-here"
    REFRESH_SECRET_KEY: str = "your-refresh-secret-key-here"
    ALGORITHM: str = "HS256"
    
    # 토큰 만료 시간 설정
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth2 설정
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./test.db"
    TEST_DATABASE_URL: str = "sqlite:///./test.db"
    
    # 배포 환경 설정
    ENVIRONMENT: str = "development"
    
    # 프론트엔드 URL (CORS용)
    FRONTEND_URL: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()