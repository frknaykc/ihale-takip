from typing import List, Dict, Any, AsyncGenerator
from .scrapers.base_models import ScrapedTender
from .scrapers import (
    dmo_scraper, turksat_scraper, teias_scraper, botas_scraper,
    tpao_scraper, tedas_scraper, jandarma_scraper, euas_scraper,
    egm_scraper, ptt_scraper
)

class ScraperService:
    """İhale scraper'larını yöneten servis"""
    def __init__(self):
        self.scrapers = {
            'dmo': dmo_scraper,
            'turksat': turksat_scraper,
            'teias': teias_scraper,
            'botas': botas_scraper,
            'tpao': tpao_scraper,
            'tedas': tedas_scraper,
            'jandarma': jandarma_scraper,
            'euas': euas_scraper,
            'egm': egm_scraper,
            'ptt': ptt_scraper
        }

    async def scrape_all(self) -> AsyncGenerator[ScrapedTender, None]:
        """Tüm kaynaklardan ihale verilerini çeker"""
        for scraper in self.scrapers.values():
            try:
                async for tender in scraper.scrape():
                    yield tender
            except Exception as e:
                print(f"Error scraping {scraper.__name__}: {str(e)}")
                continue

    async def scrape_source(self, source_slug: str) -> AsyncGenerator[ScrapedTender, None]:
        """Belirli bir kaynaktan ihale verilerini çeker"""
        if source_slug not in self.scrapers:
            raise ValueError(f"Unknown source: {source_slug}")
        
        scraper = self.scrapers[source_slug]
        async for tender in scraper.scrape():
            yield tender

    def get_sources(self) -> List[Dict[str, Any]]:
        """Mevcut kaynakların listesini döndürür"""
        return [
            {"id": i+1, "name": name.upper(), "slug": name, "url": ""}
            for i, name in enumerate(self.scrapers.keys())
        ]

scraper_service = ScraperService()
