from fastapi import APIRouter, Depends, Query
from google.cloud import storage
from datetime import timedelta
import os

router = APIRouter()

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

@router.get("/signed-url")
def get_signed_url(filename: str = Query(...)):
    """Devuelve signed URL para subir y la URL pública"""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)

    # URL para subir (PUT)
    upload_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=10),  # expira en 10 minutos
        method="PUT",
        content_type="application/octet-stream",
    )

    # URL pública (depende si el bucket está público o no)
    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {"upload_url": upload_url, "public_url": public_url}
