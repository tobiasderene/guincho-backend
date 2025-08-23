from fastapi import APIRouter, Depends, Query, HTTPException, status
from google.cloud import storage
from google.auth.transport import requests
from google.auth import default, compute_engine
from datetime import timedelta
import os
from sqlalchemy.orm import Session
from app.core.security import get_current_user 
from app.db.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

credentials, _ = default()

# then within your abstraction
auth_request = requests.Request()
credentials.refresh(auth_request)

signing_credentials = compute_engine.IDTokenCredentials(
    auth_request,
    "",
    service_account_email=credentials.service_account_email
)

@router.get("/signed-url")
def get_signed_url(
    filename: str = Query(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El parámetro filename es obligatorio."
            )

        logger.info(f"Generando signed URL para: {filename}")
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)

        upload_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=10),
            method="PUT",
            credentials=signing_credentials,
        )

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        logger.info(f"URL generada correctamente: {upload_url}")

        return {"upload_url": upload_url, "public_url": public_url}

    except Exception as e:
        logger.exception("Error generando signed URL")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )