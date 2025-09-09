import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from datetime import datetime
from jinja2 import Environment, PackageLoader, select_autoescape
import os

from .scrapers.base_models import ScrapedTender
from ..config import settings

class EmailService:
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader('app', 'services/email_templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def send_email(self, subject: str, recipients: List[str], template_name: str, **template_vars):
        """Email gönderme işlemini gerçekleştirir"""
        template = self.env.get_template(f"{template_name}.html")
        html_content = template.render(**template_vars)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.DEFAULT_SENDER
        msg['To'] = ', '.join(recipients)
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

    async def send_tender_notification(self, tenders: List[ScrapedTender]):
        """Yeni ihaleler için bildirim gönderir"""
        await self.send_email(
            subject="Yeni İhaleler Bulundu",
            recipients=settings.NOTIFICATION_RECIPIENTS,
            template_name="tender_notification",
            tenders=tenders,
            date=datetime.now().strftime("%d.%m.%Y %H:%M")
        )

    async def send_no_new_tenders_notification(self):
        """Yeni ihale bulunamadığında bildirim gönderir"""
        await self.send_email(
            subject="Yeni İhale Bulunamadı",
            recipients=settings.NOTIFICATION_RECIPIENTS,
            template_name="no_new_tenders",
            date=datetime.now().strftime("%d.%m.%Y %H:%M")
        )

    async def send_error_notification(self, error_message: str):
        """Hata durumunda bildirim gönderir"""
        await self.send_email(
            subject="İhale Takip Sistemi Hata Bildirimi",
            recipients=settings.ERROR_NOTIFICATION_RECIPIENTS,
            template_name="error_notification",
            error=error_message,
            date=datetime.now().strftime("%d.%m.%Y %H:%M")
        )

email_service = EmailService()

async def send_email(recipient: str, subject: str, html_content: str):
    """Basit email gönderme fonksiyonu"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.DEFAULT_SENDER
        msg['To'] = recipient
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
            
        print(f"✅ Email sent to {recipient}")
        
    except Exception as e:
        print(f"❌ Email sending failed to {recipient}: {e}")
        raise e