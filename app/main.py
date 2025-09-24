from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .utils import get_password_hash

from .config import settings
from .db import Base, engine, get_db
from .services.scheduler import scheduler_service
from .routers import tenders, mail, auth
from .models import User

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(title="İhale Takip API")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekle
app.include_router(auth.router, prefix="/api")
app.include_router(tenders.router, prefix="/api")
app.include_router(mail.router, prefix="/api/mail")


def create_default_admin():
    """Default admin kullanıcısını oluştur"""
    db = next(get_db())
    try:
        # Admin kullanıcısı var mı kontrol et
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            return
        
        # Default admin kullanıcısı oluştur
        hashed_password = get_password_hash("12345")
        admin_user = User(
            username="admin",
            email="admin@infrasis.com",
            hashed_password=hashed_password,
            full_name="Sistem Yöneticisi",
            is_active=True,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        print("✅ Default admin kullanıcısı oluşturuldu (admin/12345)")
        
    except Exception as e:
        print(f"❌ Admin kullanıcısı oluşturulurken hata: {e}")
    finally:
        db.close()

# Uygulama başlatıldığında zamanlayıcıyı başlat
@app.on_event("startup")
async def startup_event():
    create_default_admin()
    scheduler_service.start()

# Uygulama kapatıldığında zamanlayıcıyı durdur
@app.on_event("shutdown")
async def shutdown_event():
    scheduler_service.stop()