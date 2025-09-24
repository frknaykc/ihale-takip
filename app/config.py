from pydantic_settings import BaseSettings
from typing import List
from pydantic import EmailStr, field_validator
import json

class Settings(BaseSettings):
    # Database ayarları
    DATABASE_URL: str = "sqlite:///./data.db"
    
    # Scraper ayarları
    SCRAPE_INTERVAL_MINUTES: int = 180
    
    # Email ayarları
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "infrasis.otomasyon@gmail.com"
    SMTP_PASSWORD: str
    DEFAULT_SENDER: EmailStr = "infrasis.otomasyon@gmail.com"
    NOTIFICATION_RECIPIENTS: List[EmailStr] = ["infrasis.otomasyon@gmail.com"]
    ERROR_NOTIFICATION_RECIPIENTS: List[EmailStr] = ["infrasis.otomasyon@gmail.com"]

    # Tender filtreleme ayarları
    ALLOWED_TENDER_CATEGORIES: List[str] = ["bilisim_teknolojileri"]

    # CORS ayarları
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # JWT ayarları
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @field_validator(
        "NOTIFICATION_RECIPIENTS",
        "ERROR_NOTIFICATION_RECIPIENTS",
        "ALLOWED_TENDER_CATEGORIES",
        mode="before",
    )
    def validate_list(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()