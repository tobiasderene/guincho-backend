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

router = APIRouter()
BUCKET_NAME = os.getenv("BUCKET_NAME")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(file.filename)

        # sube el archivo al bucket
        blob.upload_from_file(file.file, content_type=file.content_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{file.filename}"

        return {"public_url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
