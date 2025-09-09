from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, engine
from .services.scheduler import scheduler_service
from .routers import tenders, mail

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
app.include_router(tenders.router, prefix="/api")
app.include_router(mail.router, prefix="/api/mail")

# Uygulama başlatıldığında zamanlayıcıyı başlat
@app.on_event("startup")
async def startup_event():
    scheduler_service.start()

# Uygulama kapatıldığında zamanlayıcıyı durdur
@app.on_event("shutdown")
async def shutdown_event():
    scheduler_service.stop()