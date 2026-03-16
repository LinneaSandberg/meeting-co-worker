import uuid
import asyncio

from fastapi import APIRouter, UploadFile, File, HTTPException

from models.job import job_store
from services.upload_service import allowed_file, save_upload
from services.job_service import run_job
from logging_config import get_app_logger

logger = get_app_logger()

router = APIRouter()


@router.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload and start async processing."""
    logger.info("Received file upload request")

    if not file.filename:
        raise HTTPException(status_code=400, detail='No file selected')

    if not allowed_file(file.filename):
        from config import ALLOWED_EXTENSIONS
        raise HTTPException(
            status_code=400,
            detail=f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        )

    try:
        filepath = await save_upload(file)
        logger.info(f"File saved: {filepath}")

        job_id = str(uuid.uuid4())
        job_store.create(job_id)

        asyncio.create_task(run_job(job_id, filepath))

        return {"job_id": job_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling file upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail='Failed to process upload')
