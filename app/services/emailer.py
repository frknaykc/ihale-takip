import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Optional, List
from datetime import datetime
from ..config import settings


def send_email(subject: str, body_html: str, recipient: str, sender: Optional[str] = None, attachment_name: Optional[str] = None, attachment_bytes: Optional[bytes] = None) -> None:
	msg = MIMEMultipart()
	msg["From"] = sender or settings.smtp_from or settings.smtp_user
	msg["To"] = recipient
	msg["Subject"] = subject

	msg.attach(MIMEText(body_html, "html", "utf-8"))

	if attachment_bytes and attachment_name:
		part = MIMEApplication(attachment_bytes, Name=attachment_name)
		part["Content-Disposition"] = f'attachment; filename="{attachment_name}"'
		msg.attach(part)

	with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
		server.connect(settings.smtp_host, settings.smtp_port)
		server.ehlo()
		server.starttls()
		server.ehlo()
		if settings.smtp_user and settings.smtp_password:
			server.login(settings.smtp_user, settings.smtp_password)
		server.send_message(msg)


def send_tender_email(recipient: str, sender: str, subject: str, tenders: List, attachment_name: Optional[str] = None, attachment_bytes: Optional[bytes] = None) -> None:
	"""İhale listesi ile mail gönder"""
	
	# HTML template
	html_body = f"""
	<!DOCTYPE html>
	<html>
	<head>
		<meta charset="utf-8">
		<title>{subject}</title>
		<style>
			body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
			.container {{ background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
			.header {{ color: #2563eb; border-bottom: 2px solid #e5e7eb; padding-bottom: 15px; margin-bottom: 20px; }}
			.tender {{ border: 1px solid #e5e7eb; border-radius: 6px; padding: 15px; margin-bottom: 15px; background-color: #fafafa; }}
			.tender-title {{ font-weight: bold; color: #1f2937; margin-bottom: 8px; }}
			.tender-meta {{ font-size: 12px; color: #6b7280; margin-bottom: 8px; }}
			.tender-desc {{ font-size: 14px; color: #374151; line-height: 1.4; }}
			.tender-link {{ display: inline-block; margin-top: 10px; padding: 8px 16px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; }}
			.footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; text-align: center; }}
		</style>
	</head>
	<body>
		<div class="container">
			<div class="header">
				<h2>🏛️ İhale Takip Sistemi</h2>
				<p><strong>{subject}</strong></p>
				<p>Gönderen: {sender}</p>
				<p>Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
				<p>Toplam İhale: {len(tenders)}</p>
			</div>
			
			<div class="tenders">
	"""
	
	# İhaleleri ekle
	for i, tender in enumerate(tenders, 1):  # Tüm ihaleler
		source_name = tender.source.name if tender.source else 'Bilinmeyen'
		published_date = tender.published_at.strftime('%d.%m.%Y') if tender.published_at else 'Tarih yok'
		
		description = tender.description[:200] + '...' if tender.description and len(tender.description) > 200 else (tender.description or '')
		
		html_body += f"""
				<div class="tender">
					<div class="tender-title">{i}. {tender.title}</div>
					<div class="tender-meta">
						🏢 Kaynak: {source_name} | 📅 Yayın Tarihi: {published_date}
					</div>
					<div class="tender-desc">{description}</div>
					<a href="{tender.url}" target="_blank" class="tender-link">📄 İhale Detayları</a>
				</div>
		"""
	
	# Tüm ihaleler gösteriliyor
	
	html_body += f"""
			</div>
			
			<div class="footer">
				<p>🏛️ Türkiye Kamu İhaleleri Takip Sistemi</p>
				<p>Bu mail otomatik olarak gönderilmiştir.</p>
				<p><small>Güncel veriler ve otomatik takip ile ihale fırsatlarını kaçırmayın</small></p>
			</div>
		</div>
	</body>
	</html>
	"""
	
	send_email(
		subject=subject,
		body_html=html_body,
		recipient=recipient,
		sender=sender,
		attachment_name=attachment_name,
		attachment_bytes=attachment_bytes
	)
