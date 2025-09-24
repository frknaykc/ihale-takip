from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, time, timedelta
from enum import Enum
import uuid

from ..db import get_db
from .. import models, crud
from ..services.emailer import send_tender_email

router = APIRouter(prefix="/api/mail", tags=["mail_automation"])

class ScheduleType(str, Enum):
    ONCE = "once"
    DAILY = "daily" 
    WEEKLY = "weekly"

class MailScheduleRequest(BaseModel):
    sender_email: EmailStr
    recipient_emails: List[EmailStr]
    subject: str
    schedule_type: ScheduleType
    scheduled_time: Optional[str] = None  # HH:MM format
    scheduled_date: Optional[str] = None  # YYYY-MM-DD format
    filters: dict = {}
    is_active: bool = True

class MailScheduleResponse(BaseModel):
    id: str
    sender_email: str
    recipient_emails: List[str]
    subject: str
    schedule_type: str
    scheduled_time: Optional[str]
    scheduled_date: Optional[str]
    filters: dict
    is_active: bool
    created_at: datetime
    last_sent: Optional[datetime]
    next_run: Optional[datetime]

class ManualMailRequest(BaseModel):
    sender_email: EmailStr
    recipient_emails: List[EmailStr]
    subject: str
    filters: dict = {}

# In-memory storage for mail schedules (gerçek uygulamada database kullanılmalı)
mail_schedules = {}

@router.post("/send-manual")
async def send_manual_mail(
    request: ManualMailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manuel mail gönderimi"""
    try:
        # İhale verilerini filtrele
        tenders = crud.filter_tenders(
            db=db,
            query=request.filters.get("query", ""),
            source_slug=request.filters.get("source_slug", ""),
            date_from=request.filters.get("date_from"),
            date_to=request.filters.get("date_to"),
            limit=request.filters.get("limit", 100),
            offset=0,
        )
        
        # Her alıcıya mail gönder
        for recipient in request.recipient_emails:
            background_tasks.add_task(
                send_tender_email,
                recipient=recipient,
                sender=request.sender_email,
                subject=request.subject,
                tenders=tenders
            )
        
        return {
            "success": True,
            "message": f"{len(request.recipient_emails)} alıcıya mail gönderildi",
            "tender_count": len(tenders)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mail gönderimi hatası: {str(e)}")

@router.post("/schedule", response_model=MailScheduleResponse)
async def create_mail_schedule(request: MailScheduleRequest):
    """Mail otomasyonu planla"""
    schedule_id = str(uuid.uuid4())
    
    # Sonraki çalışma zamanını hesapla
    next_run = None
    if request.schedule_type == ScheduleType.ONCE and request.scheduled_date and request.scheduled_time:
        next_run = datetime.strptime(f"{request.scheduled_date} {request.scheduled_time}", "%Y-%m-%d %H:%M")
    elif request.schedule_type == ScheduleType.DAILY and request.scheduled_time:
        # Bugün veya yarın aynı saatte
        today = datetime.now().date()
        scheduled_time = datetime.strptime(request.scheduled_time, "%H:%M").time()
        next_run = datetime.combine(today, scheduled_time)
        if next_run <= datetime.now():
            next_run = datetime.combine(today, scheduled_time) + timedelta(days=1)
    
    schedule = {
        "id": schedule_id,
        "sender_email": request.sender_email,
        "recipient_emails": request.recipient_emails,
        "subject": request.subject,
        "schedule_type": request.schedule_type,
        "scheduled_time": request.scheduled_time,
        "scheduled_date": request.scheduled_date,
        "filters": request.filters,
        "is_active": request.is_active,
        "created_at": datetime.now(),
        "last_sent": None,
        "next_run": next_run
    }
    
    mail_schedules[schedule_id] = schedule
    
    return MailScheduleResponse(**schedule)

@router.get("/schedules", response_model=List[MailScheduleResponse])
async def get_mail_schedules():
    """Tüm mail planlarını listele"""
    return [MailScheduleResponse(**schedule) for schedule in mail_schedules.values()]

@router.delete("/schedules/{schedule_id}")
async def delete_mail_schedule(schedule_id: str):
    """Mail planını sil"""
    if schedule_id not in mail_schedules:
        raise HTTPException(status_code=404, detail="Mail planı bulunamadı")
    
    del mail_schedules[schedule_id]
    return {"success": True, "message": "Mail planı silindi"}

@router.put("/schedules/{schedule_id}/toggle")
async def toggle_mail_schedule(schedule_id: str):
    """Mail planını aktif/pasif yap"""
    if schedule_id not in mail_schedules:
        raise HTTPException(status_code=404, detail="Mail planı bulunamadı")
    
    mail_schedules[schedule_id]["is_active"] = not mail_schedules[schedule_id]["is_active"]
    
    return {
        "success": True,
        "is_active": mail_schedules[schedule_id]["is_active"]
    }

@router.post("/test")
async def test_mail_settings(
    sender_email: EmailStr,
    recipient_email: EmailStr,
    background_tasks: BackgroundTasks
):
    """Mail ayarlarını test et"""
    try:
        from ..services.emailer import send_email
        
        subject = "İhale Takip Sistemi - Test Maili"
        body = f"""
        <h2>Test Maili</h2>
        <p>Bu bir test mailidir.</p>
        <p>Gönderen: {sender_email}</p>
        <p>Alıcı: {recipient_email}</p>
        <p>Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        <hr>
        <p><small>İhale Takip Sistemi</small></p>
        """
        
        await send_email(
            recipient=recipient_email,
            sender=sender_email,
            subject=subject,
            body_html=body
        )
        
        return {"success": True, "message": "Test maili gönderildi"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test maili hatası: {str(e)}")
