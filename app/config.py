
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # App settings
    DEBUG: bool = True
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./data/jirani_library.db"
    
    # Security settings
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
