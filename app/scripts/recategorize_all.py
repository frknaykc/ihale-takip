from sqlalchemy.orm import Session
from ..db import get_db, engine
from ..models import Tender
from ..lib.categories import classifyTender

def recategorize_all_tenders():
    """Tüm ihaleleri yeniden kategorize et"""
    db = Session(engine)
    try:
        # Tüm ihaleleri al
        tenders = db.query(Tender).all()
        print(f"Toplam {len(tenders)} ihale bulundu.")
        
        # Her ihaleyi kategorize et
        for tender in tenders:
            old_category = tender.category
            new_category = classifyTender(tender.title, tender.description or "")
            
            if old_category != new_category:
                tender.category = new_category
                print(f"ID: {tender.id} - Eski: {old_category} -> Yeni: {new_category}")
                print(f"Başlık: {tender.title}")
                print("-" * 80)
        
        # Değişiklikleri kaydet
        db.commit()
        print("\nKategorizasyon tamamlandı!")
        
    except Exception as e:
        print(f"Hata oluştu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    recategorize_all_tenders()
