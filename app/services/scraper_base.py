from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Iterable, Optional, AsyncGenerator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time


class ScrapedTender:
	def __init__(self, title: str, url: str, description: Optional[str] = None, published_at: Optional[datetime] = None):
		self.title = title
		self.url = url
		self.description = description
		self.published_at = published_at


class BaseScraper:
	name: str
	slug: str
	base_url: str

	def __init__(self, name: str, slug: str, base_url: str):
		self.name = name
		self.slug = slug
		self.base_url = base_url

	async def fetch_html(self, url: str) -> str:
		async with httpx.AsyncClient(
			timeout=30.0,
			verify=False,  # SSL sertifika doğrulamasını atla
			headers={
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
			}
		) as client:
			resp = await client.get(url)
			resp.raise_for_status()
			return resp.text

	def fetch_html_with_selenium(self, url: str, wait_for_element: str = None, timeout: int = 10) -> str:
		"""Selenium kullanarak JavaScript render edilen HTML'i al"""
		options = Options()
		options.add_argument('--headless')  # Arka planda çalıştır
		options.add_argument('--no-sandbox')
		options.add_argument('--disable-dev-shm-usage')
		options.add_argument('--disable-gpu')
		options.add_argument('--window-size=1920,1080')
		options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
		
		driver = None
		try:
			# ChromeDriver'ı otomatik indir ve kullan
			driver = webdriver.Chrome(
				service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
				options=options
			)
			
			driver.get(url)
			
			# Belirli bir element bekle (opsiyonel)
			if wait_for_element:
				WebDriverWait(driver, timeout).until(
					EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
				)
			else:
				# Genel olarak sayfa yüklenmesini bekle
				time.sleep(3)
			
			html = driver.page_source
			return html
			
		except Exception as e:
			print(f"Selenium hatası ({url}): {e}")
			# Selenium başarısız olursa normal httpx ile dene
			import asyncio
			return asyncio.run(self.fetch_html(url))
		finally:
			if driver:
				driver.quit()

	async def scrape(self) -> list[ScrapedTender]:
		html = await self.fetch_html(self.base_url)
		soup = BeautifulSoup(html, "lxml")
		results = []
		async for tender in self.parse(soup):
			results.append(tender)
		return results

	async def parse(self, soup: BeautifulSoup) -> AsyncGenerator[ScrapedTender, None]:
		raise NotImplementedError("parse must be implemented by subclasses")
