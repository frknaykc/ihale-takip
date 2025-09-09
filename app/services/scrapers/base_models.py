from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ScrapedTender(BaseModel):
    """Scraper'ların döndürdüğü ihale modeli"""
    title: str
    url: str
    source: str
    source_name: str
    published_at: Optional[datetime] = None
    description: Optional[str] = None
    category: Optional[str] = None
