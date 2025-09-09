from datetime import datetime
from typing import AsyncGenerator, Any
import re
import httpx
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from ..scraper_base import BaseScraper, ScrapedTender

# lxml parser'ı kullan
PARSER = "lxml"


class JandarmaScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            name="Jandarma",
            slug="jandarma", 
            base_url="https://vatandas.jandarma.gov.tr/ihalesorgu/"
        )
    
    async def fetch_html(self, url: str) -> str:
        """İhale listesi sayfasını çek"""
        try:
            # İhale listesi sayfasının URL'i
            LIST = urljoin(self.base_url, "FORM/FrmIhaleListe.aspx")
            
            print(f"Jandarma: İstek atılacak URL: {LIST}")
            
            # HTTP istemcisini yapılandır
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Referer": "https://vatandas.jandarma.gov.tr/ihalesorgu/",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            print("Jandarma: HTTP başlıkları:", headers)
            
            # Session oluştur
            async with httpx.AsyncClient(
                headers=headers, 
                follow_redirects=True, 
                timeout=30.0, 
                http2=False,
                verify=False  # SSL hatalarını geçici olarak devre dışı bırak
            ) as client:
                # İstek öncesi bekleme
                await asyncio.sleep(1)
                
                # İstek gönder
                print("Jandarma: İstek gönderiliyor...")
                response = await client.get(LIST)
                print(f"Jandarma: İstek durumu: {response.status_code}")
                print(f"Jandarma: Response başlıkları: {dict(response.headers)}")
                
                # Encoding'i kontrol et ve düzelt
                if not response.encoding or response.encoding.lower() in ("iso-8859-1", "ascii"):
                    response.encoding = response.apparent_encoding or "utf-8"
                print(f"Jandarma: Response encoding: {response.encoding}")
                
                html = response.text
                print(f"Jandarma: Response uzunluğu: {len(html)} karakter")
                
                # Ham HTML'de PSN sayısını kontrol et
                psn_count = html.count("frmIhale.aspx?PSN=")
                print(f"Jandarma: Ham HTML'de {psn_count} PSN linki var")
                print(f"Jandarma: İlk 500 karakter:\n{html[:500]}")
                print(f"Jandarma: Son 500 karakter:\n{html[-500:]}")
                
                return html
                
        except Exception as e:
            print(f"Jandarma: Liste sayfası çekme hatası: {e}")
            print(f"Jandarma: Hata detayı: {str(e)}")
            import traceback
            print(f"Jandarma: Hata stack trace:\n{traceback.format_exc()}")
            return ""
    
    async def parse(self, soup: BeautifulSoup) -> AsyncGenerator[ScrapedTender, None]:
        """İhaleleri parse et"""
        # CSS select yerine regex'li find_all kullan
        links = soup.find_all("a", href=re.compile(r"^frmIhale\.aspx\?PSN="))
        print(f"Jandarma: BeautifulSoup ile {len(links)} ihale linki bulundu")
        
        for a in links:
            try:
                # İhale başlığı
                title = a.get_text(strip=True)
                if not title:
                    continue
                
                # İhale detay URL'i
                href = a["href"]
                url = urljoin("https://vatandas.jandarma.gov.tr/ihalesorgu/FORM/", href)
                
                # İhale satırından bilgileri al
                row = a.find_parent("tr")
                tds = row.find_all("td") if row else []
                date_text = tds[1].get_text(strip=True) if len(tds) > 1 else ""
                description = tds[2].get_text(strip=True) if len(tds) > 2 else ""
                
                # Konum: bir üst td → oradaki ilk span (mavi başlık)
                td = row.find_parent("td") if row else None
                loc_span = td.find("span", id=re.compile("etkIhlYer")) if td else None
                location = loc_span.get_text(strip=True) if loc_span else None
                
                # Tarih
                published_at = self.parse_date(date_text) if date_text else None
                
                # Tam açıklama oluştur
                full_description = f"Jandarma İhalesi"
                if location:
                    full_description += f"\nBölge: {location}"
                if description:
                    full_description += f"\nDetay: {description}"
                if published_at:
                    full_description += f"\nİhale Tarihi: {published_at.strftime('%d.%m.%Y %H:%M')}"
                
                yield ScrapedTender(
                    title=title,
                    url=url,
                    description=full_description,
                    published_at=published_at
                )
                
            except Exception as e:
                print(f"Jandarma: İhale parse hatası: {e}")
                continue
    
    def parse_date(self, date_str: str) -> datetime | None:
        """Jandarma tarih formatını parse et (27.8.2025 09:00:00)"""
        if not date_str:
            return None
        
        try:
            # "27.8.2025 09:00:00" formatı
            if re.match(r'\d{1,2}\.\d{1,2}\.\d{4}\s+\d{1,2}:\d{2}:\d{2}', date_str):
                return datetime.strptime(date_str, '%d.%m.%Y %H:%M:%S')
            
            # "27.8.2025" formatı (saat olmadan)
            elif re.match(r'\d{1,2}\.\d{1,2}\.\d{4}', date_str):
                return datetime.strptime(date_str, '%d.%m.%Y')
                
        except ValueError as e:
            print(f"Jandarma: Tarih parse hatası '{date_str}': {e}")
        
        return None