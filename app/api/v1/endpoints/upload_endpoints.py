from fastapi import APIRouter, Depends, Query, HTTPException, status
from google.cloud import storage
from datetime import timedelta
import os
from sqlalchemy.orm import Session
from app.core.security import get_current_user 
from app.db.database import get_db


router = APIRouter()

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

@router.get("/signed-url")
def get_signed_url(
    filename: str = Query(...),
    current_user: dict = Depends(get_current_user),  # ✅ Solo usuarios logueados
    db: Session = Depends(get_db),
):
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro filename es obligatorio."
        )

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)

    # URL temporal para subir archivo (PUT)
    upload_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=10),  # dura 10 min
        method="PUT",
        content_type="application/octet-stream",
    )

    # URL pública (para guardarla en la DB)
    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {"upload_url": upload_url, "public_url": public_url}