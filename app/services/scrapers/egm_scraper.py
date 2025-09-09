from datetime import datetime
from typing import AsyncGenerator, Any
import re
import httpx
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import BytesIO
from PIL import Image
import pytesseract
from ..scraper_base import BaseScraper, ScrapedTender

class EGMScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            name="EGM",
            slug="egm",
            base_url="https://www.egm.gov.tr/destekhizmetleri/ihale-takvimi"
        )
    
    async def fetch_html(self, url: str) -> str:
        """İhale listesi sayfasını çek"""
        try:
            print(f"EGM: İstek atılacak URL: {url}")
            
            # HTTP istemcisini yapılandır
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            print("EGM: HTTP başlıkları:", headers)
            
            # Session oluştur
            async with httpx.AsyncClient(
                headers=headers, 
                follow_redirects=True, 
                timeout=30.0,
                verify=False  # SSL hatalarını geçici olarak devre dışı bırak
            ) as client:
                # İstek öncesi bekleme
                await asyncio.sleep(1)
                
                # İstek gönder
                print("EGM: İstek gönderiliyor...")
                response = await client.get(url)
                print(f"EGM: İstek durumu: {response.status_code}")
                print(f"EGM: Response başlıkları: {dict(response.headers)}")
                
                html = response.text
                print(f"EGM: Response uzunluğu: {len(html)} karakter")
                
                return html
                
        except Exception as e:
            print(f"EGM: Liste sayfası çekme hatası: {e}")
            print(f"EGM: Hata detayı: {str(e)}")
            import traceback
            print(f"EGM: Hata stack trace:\n{traceback.format_exc()}")
            return ""
    
    async def fetch_image(self, url: str) -> bytes:
        """İhale tablosu resmini çek"""
        try:
            print(f"EGM: Resim çekiliyor: {url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": self.base_url
            }
            
            async with httpx.AsyncClient(headers=headers, timeout=30.0, verify=False) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
                
        except Exception as e:
            print(f"EGM: Resim çekme hatası: {e}")
            return None
    
    def parse_image(self, image_bytes: bytes) -> list[dict]:
        """Resimden ihale bilgilerini çıkar"""
        try:
            # Resmi aç
            image = Image.open(BytesIO(image_bytes))
            
            # OCR yap
            text = pytesseract.image_to_string(image, lang='tur')
            print(f"EGM: OCR sonucu:\n{text}")
            
            # Satırlara böl
            lines = text.split('\n')
            
            # İhale bilgilerini topla
            tenders = []
            current_tender = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Tarih kontrolü
                date_match = re.match(r'(\d{2}\.\d{2}\.\d{4})', line)
                if date_match:
                    if current_tender:
                        tenders.append(current_tender)
                    current_tender = {'date': date_match.group(1)}
                    continue
                
                # İhale başlığı ve açıklaması
                if current_tender:
                    if 'title' not in current_tender:
                        current_tender['title'] = line
                    else:
                        current_tender['description'] = current_tender.get('description', '') + '\n' + line
            
            # Son ihaleyi ekle
            if current_tender:
                tenders.append(current_tender)
            
            return tenders
            
        except Exception as e:
            print(f"EGM: Resim parse hatası: {e}")
            return []
    
    async def parse(self, soup: BeautifulSoup) -> AsyncGenerator[ScrapedTender, None]:
        """İhaleleri parse et"""
        try:
            # Resim URL'lerini bul
            image_urls = []
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if 'IcSite/destekhizmetleri' in src and src.endswith('.png'):
                    image_urls.append(urljoin(self.base_url, src))
            
            print(f"EGM: {len(image_urls)} ihale tablosu resmi bulundu")
            
            # Her resmi işle
            for image_url in image_urls:
                # Resmi çek
                image_bytes = await self.fetch_image(image_url)
                if not image_bytes:
                    continue
                
                # Resmi parse et
                tenders = self.parse_image(image_bytes)
                print(f"EGM: {len(tenders)} ihale bulundu")
                
                # İhaleleri yield et
                for tender in tenders:
                    try:
                        # Tarihi parse et
                        published_at = datetime.strptime(tender['date'], '%d.%m.%Y')
                        
                        # Açıklama oluştur
                        description = f"EGM İhalesi\nTarih: {tender['date']}"
                        if 'description' in tender:
                            description += f"\nDetay: {tender['description']}"
                        
                        yield ScrapedTender(
                            title=tender['title'],
                            url=image_url,  # Resmin URL'i
                            description=description,
                            published_at=published_at
                        )
                        
                    except Exception as e:
                        print(f"EGM: İhale parse hatası: {e}")
                        continue
                
        except Exception as e:
            print(f"EGM: Parse hatası: {e}")
            return
