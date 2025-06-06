from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # JWT 설정
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ALGORITHM: str
    
    # 토큰 만료 시간 설정
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Google OAuth2 설정
    GOOGLE_CLIENT_ID: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()