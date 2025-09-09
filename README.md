# İhale Takip Sistemi

Bu proje, Türkiye'deki çeşitli kamu kurumlarının ihale ilanlarını otomatik olarak toplayan ve yöneten bir web uygulamasıdır.

## Özellikler

- 9 farklı kamu kurumundan ihale verilerini otomatik toplama
- Yinelenen ihaleleri tespit etme ve filtreleme
- Web arayüzü ile ihale arama ve filtreleme
- CSV formatında dışa aktarma
- Email ile ihale listesi gönderme
- Günde birkaç kez otomatik tarama

## Kurulum

### Backend

1. Virtual environment oluşturun:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

3. (Opsiyonel) Email ayarları için `.env` dosyası oluşturun:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com
SCRAPE_INTERVAL_MINUTES=180
```

4. Sunucuyu başlatın:
```bash
uvicorn app.main:app --reload
```

### Frontend (Next.js)

1. Frontend klasörüne gidin:
```bash
cd frontend
```

2. Bağımlılıkları yükleyin:
```bash
npm install
```

3. Next.js geliştirme sunucusunu başlatın:
```bash
npm run dev
```

## Kullanım

1. Backend sunucu http://127.0.0.1:8000 adresinde çalışır
2. Frontend http://localhost:3000 adresinde çalışır (Next.js)
3. Web arayüzünden ihaleleri arayabilir, filtreleleyebilir ve dışa aktarabilirsiniz

## API Endpoints

- `GET /api/admin/health` - Sistem durumu
- `POST /api/tenders/search` - İhale arama
- `GET /api/tenders/sources` - Kaynak listesi
- `POST /api/tenders/export.csv` - CSV dışa aktarma
- `POST /api/tenders/email` - Email gönderme
- `POST /api/tenders/scrape-now` - Anında tarama

## İzlenen Kaynaklar

1. DMO (Devlet Malzeme Ofisi)
2. Türksat
3. TEİAŞ (Türkiye Elektrik İletim A.Ş.)
4. TEDAŞ (Türkiye Elektrik Dağıtım A.Ş.)
5. PTT
6. Jandarma
7. BOTAŞ
8. EÜAŞ (Elektrik Üretim A.Ş.)
9. TPAO (Türkiye Petrolleri A.O.)

## Geliştirme

## Scraper Geliştirme

### Mevcut Durum
- ✅ **DMO, Türksat, TEİAŞ, PTT**: Mock verilerle çalışıyor
- ⚠️ **TEDAŞ, Jandarma, BOTAŞ, EÜAŞ, TPAO**: Stub scraper (veri çekmiyor)

### Gerçek Scraper Implementasyonu

DMO scraper örneği gerçek HTML yapısına göre yazıldı ama JavaScript ile yüklenen tablolar için Selenium gerekebilir.

#### 1. Selenium Kurulumu
```bash
pip install selenium webdriver-manager
```

#### 2. Selenium ile Scraper Örneği
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class RealDMOScraper(BaseScraper):
    async def fetch_html(self, url: str) -> str:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)
            # JavaScript tablosunun yüklenmesini bekle
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "sample_1"))
            )
            return driver.page_source
        finally:
            driver.quit()
```

#### 3. Site Analizi Adımları
1. **Developer Tools** → Network tab → XHR/Fetch requests
2. **JavaScript API calls** → JSON responses
3. **Table loading patterns** → Dynamic content timing
4. **CSRF tokens** → Form submissions

### Yeni Scraper Ekleme

`app/services/scrapers/` klasöründe yeni scraper oluşturun:

```python
from ..scraper_base import BaseScraper, ScrapedTender

class YeniScraper(BaseScraper):
    def __init__(self):
        super().__init__(name="Site Adı", slug="slug", base_url="https://...")
    
    def parse(self, soup):
        # HTML parsing logic
        yield ScrapedTender(title="...", url="...", description="...", published_at=...)
```

Sonra `scrape_manager.py`'de import edip SCRAPERS listesine ekleyin.
