from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
import json
import os
from typing import List, Optional

from .scrapers.base_models import ScrapedTender
from .scraper_service import scraper_service
from .email_service import email_service
from ..models.schedule import ScheduleConfig

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.cached_tenders: List[ScrapedTender] = []
        self.config_file = "schedule_config.json"

    def start(self):
        """Zamanlayıcıyı başlatır ve varsa kayıtlı programı yükler"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = ScheduleConfig.model_validate_json(f.read())
                self.update_schedule(config)
        
        self.scheduler.start()

    def stop(self):
        """Zamanlayıcıyı durdurur"""
        self.scheduler.shutdown()

    def update_schedule(self, config: ScheduleConfig):
        """Mail gönderim zamanlarını günceller"""
        # Mevcut tüm görevleri temizle
        self.scheduler.remove_all_jobs()
        
        if not config.is_active:
            return

        # Her saat için yeni bir görev oluştur
        for time_str in config.times:
            hour, minute = map(int, time_str.split(':'))
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone='Europe/Istanbul'
            )
            self.scheduler.add_job(
                self.check_and_notify,
                trigger=trigger,
                id=f"mail_job_{hour}_{minute}"
            )

        # Konfigürasyonu kaydet
        with open(self.config_file, 'w') as f:
            f.write(config.model_dump_json())

    async def check_and_notify(self):
        """Yeni ihaleleri kontrol eder ve mail gönderir"""
        new_tenders = []
        try:
            async for tender in scraper_service.scrape_all():
                if tender not in self.cached_tenders:
                    new_tenders.append(tender)
            
            if new_tenders:
                await email_service.send_tender_notification(new_tenders)
                self.cached_tenders = new_tenders
            else:
                await email_service.send_no_new_tenders_notification()
                
        except Exception as e:
            await email_service.send_error_notification(str(e))

scheduler_service = SchedulerService()