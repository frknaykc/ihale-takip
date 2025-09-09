from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
def health():
	return {"status": "ok"}


@router.get("/version")
def version():
	return {"version": "0.1.0"}
