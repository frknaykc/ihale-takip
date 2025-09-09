from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from ..db import SessionLocal
from .. import crud, models
from .scraper_base import BaseScraper, ScrapedTender
from .scrapers.dmo_scraper import DMOScraper
from .scrapers.turksat_scraper import TurksatScraper
from .scrapers.teias_scraper import TEIASScraper
from .scrapers.ptt_scraper import PTTScraper
from .scrapers.tpao_scraper import TPAOScraper
from .scrapers.tedas_scraper import TEDASScraper
from .scrapers.jandarma_scraper import JandarmaScraper
from .scrapers.botas_scraper import BOTASScraper
from .scrapers.euas_scraper import EUASScraper
from .scrapers.egm_scraper import EGMScraper


class StubScraper(BaseScraper):
	def parse(self, soup):
		return []


SCRAPERS: List[BaseScraper] = [
	DMOScraper(),
	TurksatScraper(),
	TEIASScraper(),
	PTTScraper(),
	TPAOScraper(),
	TEDASScraper(),
	JandarmaScraper(),
	BOTASScraper(),
	EUASScraper(),
	EGMScraper(),
]


async def run_all_scrapers(sites: List[str] = None) -> int:
    inserted = 0
    with SessionLocal() as db:
        # Hangi scraperları çalıştıracağımızı belirle
        scrapers_to_run = SCRAPERS
        if sites:
            scrapers_to_run = [s for s in SCRAPERS if s.slug in sites]
            
        for s in scrapers_to_run:
            try:
                print(f"Scraping {s.name}...")
                source = crud.ensure_source(db, name=s.name, url=s.base_url, slug=s.slug)
                items = await s.scrape()
                
                scraper_count = 0
                for it in items:
                    try:
                        created = crud.create_tender_if_new(
                            db=db,
                            source=source,
                            title=it.title,
                            url=it.url,
                            description=it.description,
                            published_at=it.published_at,
                        )
                        if created:
                            inserted += 1
                            scraper_count += 1
                    except Exception as e:
                        print(f"Error creating tender from {s.name}: {e}")
                        continue
                
                print(f"✓ {s.name}: {scraper_count} new tenders added")
                
            except Exception as e:
                print(f"✗ Error scraping {s.name}: {e}")
                continue
    
    print(f"Total: {inserted} new tenders added")
    return inserted


async def trigger_scrape_once() -> int:
	return await run_all_scrapers()
