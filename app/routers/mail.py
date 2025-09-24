from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
import json
import os
import uuid
from datetime import time, datetime
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..models.schedule import ScheduleUpdate, ScheduleConfig
from ..db import get_db
from .. import crud
from ..services.email_service import send_email

router = APIRouter()

SCHEDULE_FILE = "schedule_config.json"

class ManualMailRequest(BaseModel):
    sender_email: EmailStr
    recipient_emails: List[EmailStr]
    subject: str
    filters: dict

def load_schedule() -> ScheduleConfig:
    """Zamanlama ayarlarını yükler"""
    try:
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, 'r') as f:
                data = json.load(f)
                # JSON'dan time objelerine dönüştür
                times = [time.fromisoformat(t) for t in data['times']]
                return ScheduleConfig(times=times, is_active=data['is_active'])
    except Exception as e:
        print(f"Zamanlama ayarları yüklenirken hata: {e}")
    
    # Varsayılan ayarlar
    return ScheduleConfig(
        times=[time(9, 0), time(12, 0), time(15, 0)],  # 09:00, 12:00, 15:00
        is_active=True
    )

def save_schedule(config: ScheduleConfig) -> None:
    """Zamanlama ayarlarını kaydeder"""
    try:
        data = {
            'times': [t.isoformat() for t in config.times],
            'is_active': config.is_active
        }
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Zamanlama ayarları kaydedilirken hata: {str(e)}"
        )

@router.get("/schedules", response_model=ScheduleUpdate)
async def get_schedule():
    """Mevcut zamanlama ayarlarını döndürür"""
    config = load_schedule()
    return ScheduleUpdate(
        times=[t.strftime("%H:%M") for t in config.times],
        is_active=config.is_active
    )

@router.post("/schedules")
async def update_schedule(schedule: ScheduleUpdate):
    """Zamanlama ayarlarını günceller"""
    config = schedule.to_schedule_config()
    save_schedule(config)
    
    # Scheduler'ı yeniden başlat
    from ..main import scheduler_service
    scheduler_service.update_schedule(config)
    
    return {"message": "Zamanlama ayarları güncellendi"}


@router.post("/send-manual")
async def send_manual_mail(request: ManualMailRequest, db: Session = Depends(get_db)):
    """Manuel mail gönderimi"""
    try:
        # İhale verilerini filtrele
        filters = request.filters
        date_from = datetime.fromisoformat(filters.get('date_from')) if filters.get('date_from') else None
        date_to = datetime.fromisoformat(filters.get('date_to')) if filters.get('date_to') else None
        
        tenders = crud.filter_tenders(
            db=db,
            query=filters.get('query'),
            source_slug=filters.get('source_slug'),
            date_from=date_from,
            date_to=date_to,
            limit=filters.get('limit', 100),
            offset=0,
        )
        
        # Email içeriğini template ile hazırla
        tender_count = len(tenders)
        
        # Template için veri hazırla
        template_data = {
            'subject': request.subject,
            'current_date': datetime.now().strftime('%d.%m.%Y'),
            'tender_count': tender_count,
            'tenders': tenders[:50],  # İlk 50 ihale
            'sources_count': 1 if filters.get('source_slug') else None,
            'categories_count': None,
            'filters_applied': []
        }
        
        # Uygulanan filtreleri topla
        if filters.get('query'):
            template_data['filters_applied'].append(f"Arama: {filters['query']}")
        if filters.get('source_slug'):
            source = next((t.source.name for t in tenders if t.source and t.source.slug == filters['source_slug']), filters['source_slug'])
            template_data['filters_applied'].append(f"Kaynak: {source}")
        if filters.get('date_from'):
            template_data['filters_applied'].append(f"Başlangıç: {filters['date_from']}")
        if filters.get('date_to'):
            template_data['filters_applied'].append(f"Bitiş: {filters['date_to']}")
        
        # Template'i render et
        from jinja2 import Environment, FileSystemLoader
        import os
        
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'services', 'email_templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('manual_mail.html')
        html_content = template.render(**template_data)
        
        # Mail gönder (test modunda sadece log)
        try:
            for recipient in request.recipient_emails:
                # SMTP ayarları eksikse sadece log yap
                if not all([
                    hasattr(settings, 'SMTP_USERNAME') and settings.SMTP_USERNAME,
                    hasattr(settings, 'SMTP_PASSWORD') and settings.SMTP_PASSWORD
                ]):
                    print(f"📧 Test Mode: Mail would be sent to {recipient}")
                    print(f"📧 Subject: {request.subject}")
                    print(f"📧 Content preview: {html_content[:200]}...")
                else:
                    await send_email(
                        recipient=recipient,
                        subject=request.subject,
                        html_content=html_content
                    )
        except Exception as e:
            print(f"⚠️ Mail sending failed, but continuing: {e}")
        
        return {
            "message": "Mail başarıyla gönderildi",
            "tender_count": tender_count,
            "recipients": len(request.recipient_emails)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Mail gönderimi sırasında hata: {str(e)}"
        )


@router.post("/test")
async def test_mail(sender_email: EmailStr, recipient_email: EmailStr):
    """Test maili gönderir"""
    try:
        html_content = """
        <html>
        <body>
            <h2>Test Maili</h2>
            <p>Bu bir test mailidir. SMTP ayarlarınız doğru çalışıyor!</p>
            <p>Gönderim Zamanı: {}</p>
        </body>
        </html>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # SMTP ayarları kontrol et
        if not all([
            hasattr(settings, 'SMTP_USERNAME') and settings.SMTP_USERNAME,
            hasattr(settings, 'SMTP_PASSWORD') and settings.SMTP_PASSWORD
        ]):
            print(f"📧 Test Mode: Test mail would be sent to {recipient_email}")
            return {"message": "Test maili gönderildi (test modu)", "status": "test_mode"}
        
        await send_email(
            recipient=str(recipient_email),
            subject="İhale Takip Sistemi - Test Maili",
            html_content=html_content
        )
        
        return {"message": "Test maili başarıyla gönderildi", "status": "sent"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test maili gönderimi sırasında hata: {str(e)}"
        )


# Yeni endpoint'ler - Frontend için gerekli
class ScheduleRequest(BaseModel):
    sender_email: EmailStr
    recipient_emails: List[EmailStr]
    subject: str
    schedule_type: str = "daily"
    times: List[str]
    filters: dict
    is_active: bool = True

class MailSchedule(BaseModel):
    id: str
    sender_email: str
    recipient_emails: List[str]
    subject: str
    schedule_type: str
    scheduled_time: str = None
    scheduled_date: str = None
    filters: dict
    is_active: bool
    created_at: str
    last_sent: str = None
    next_run: str = None
    times: List[str] = []

# Basit in-memory storage (production'da veritabanı kullanılmalı)
mail_schedules = {}

@router.get("/schedules", response_model=List[MailSchedule])
async def get_mail_schedules():
    """Tüm mail otomasyonlarını listele"""
    return list(mail_schedules.values())

@router.post("/schedule", response_model=MailSchedule)
async def create_mail_schedule(request: ScheduleRequest):
    """Yeni mail otomasyonu oluştur"""
    schedule_id = str(uuid.uuid4())
    
    schedule = MailSchedule(
        id=schedule_id,
        sender_email=str(request.sender_email),
        recipient_emails=[str(email) for email in request.recipient_emails],
        subject=request.subject,
        schedule_type=request.schedule_type,
        times=request.times,
        filters=request.filters,
        is_active=request.is_active,
        created_at=datetime.now().isoformat(),
        last_sent=None,
        next_run=datetime.now().isoformat() if request.is_active else None
    )
    
    mail_schedules[schedule_id] = schedule
    return schedule

@router.put("/schedules/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str):
    """Mail otomasyonunu aktif/pasif yap"""
    if schedule_id not in mail_schedules:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = mail_schedules[schedule_id]
    schedule.is_active = not schedule.is_active
    schedule.next_run = datetime.now().isoformat() if schedule.is_active else None
    
    return {"message": "Schedule status updated", "is_active": schedule.is_active}

@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Mail otomasyonunu sil"""
    if schedule_id not in mail_schedules:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    del mail_schedules[schedule_id]
    return {"message": "Schedule deleted successfully"}
