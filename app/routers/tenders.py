from fastapi import APIRouter, Depends, Response
from typing import List
import csv
import io
from ..schemas import TenderOut, TenderFilter, EmailRequest, SourceOut
from ..db import get_db
from sqlalchemy.orm import Session
from .. import crud, models
from ..services.emailer import send_email
from ..services.scrape_manager import trigger_scrape_once


router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.post("/search", response_model=List[TenderOut])
async def search_tenders(filters: TenderFilter, db: Session = Depends(get_db)):
    try:
        results = crud.filter_tenders(
            db=db,
            query=filters.query,
            source_slug=filters.source_slug,
            date_from=filters.date_from,
            date_to=filters.date_to,
            limit=filters.limit,
            offset=filters.offset,
        )
        return results
    except Exception as e:
        print(f"Tender search error: {e}")
        return []


@router.get("/sources", response_model=List[SourceOut])
def list_sources(db: Session = Depends(get_db)):
	return db.query(models.Source).all()


@router.post("/export.csv")
def export_csv(filters: TenderFilter, db: Session = Depends(get_db)):
	rows = crud.filter_tenders(
		db=db,
		query=filters.query,
		source_slug=filters.source_slug,
		date_from=filters.date_from,
		date_to=filters.date_to,
		limit=filters.limit,
		offset=filters.offset,
	)
	buf = io.StringIO()
	writer = csv.writer(buf)
	writer.writerow(["id", "title", "url", "description", "published_at", "source"])
	for t in rows:
		writer.writerow([
			t.id,
			t.title,
			t.url,
			t.description or "",
			(t.published_at.isoformat() if t.published_at else ""),
			t.source.slug if t.source else "",
		])
	csv_bytes = buf.getvalue().encode("utf-8")
	return Response(content=csv_bytes, media_type="text/csv", headers={
		"Content-Disposition": "attachment; filename=tenders.csv"
	})


@router.post("/email")
def email_results(req: EmailRequest, db: Session = Depends(get_db)):
	rows = crud.filter_tenders(
		db=db,
		query=req.query,
		source_slug=req.source_slug,
		date_from=req.date_from,
		date_to=req.date_to,
		limit=req.limit,
		offset=req.offset,
	)
	buf = io.StringIO()
	writer = csv.writer(buf)
	writer.writerow(["id", "title", "url", "description", "published_at", "source"])
	for t in rows:
		writer.writerow([
			t.id,
			t.title,
			t.url,
			t.description or "",
			(t.published_at.isoformat() if t.published_at else ""),
			t.source.slug if t.source else "",
		])
	send_email(
		subject="Ihale Sonu 7lar 3 3 3",
		body_html="<p>Ekte filtrelenen ihaleler CSV olarak gönderildi.</p>",
		recipient=req.recipient,
		attachment_name="tenders.csv",
		attachment_bytes=buf.getvalue().encode("utf-8"),
	)
	return {"status": "sent"}


@router.post("/scrape-now")
async def scrape_now():
	count = await trigger_scrape_once()
	return {"inserted": count}


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
	"""Veritabanındaki mevcut kategorileri döndür"""
	from sqlalchemy import distinct
	from ..lib.categories import categories
	
	# Veritabanından mevcut kategorileri çek
	db_categories = db.query(distinct(models.Tender.category)).filter(
		models.Tender.category.isnot(None)
	).all()
	
	# Kategori listesi oluştur
	category_list = []
	
	# Tanımlı kategorileri ekle
	for key, value in categories.items():
		category_list.append({
			"key": key,
			"name": value["name"]
		})
	
	# Veritabanından gelen diğer kategorileri ekle
	for (cat,) in db_categories:
		if cat and cat not in [c["key"] for c in category_list]:
			category_list.append({
				"key": cat,
				"name": cat.replace("_", " ").title()
			})
	
	return category_list
