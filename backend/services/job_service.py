import os
import asyncio
from functools import partial

from models.job import job_store
from config import JOB_CLEANUP_INTERVAL
from transcribe import process_meeting
from logging_config import get_app_logger

logger = get_app_logger()


async def run_job(job_id: str, filepath: str):
    """Run the transcription + extraction pipeline in a background thread."""
    try:
        def on_progress(step: str):
            if step == "transcribing":
                job_store.update(job_id, step="transcribing", progress=33)
            elif step == "extracting":
                job_store.update(job_id, step="extracting", progress=66)
            elif step == "complete":
                job_store.update(job_id, step="complete", progress=100)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(process_meeting, filepath, on_progress=on_progress)
        )

        job_store.update(
            job_id,
            step="complete",
            progress=100,
            result={
                'success': True,
                'transcript': result['transcript'],
                'insights': result['insights']
            }
        )
        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
        error_message = str(e)
        if 'API' in error_message or 'key' in error_message.lower():
            error_message = 'API error. Please check your API keys in .env file.'
        elif 'corrupted' in error_message.lower() or 'invalid_audio' in error_message:
            error_message = 'Invalid or corrupted audio file. Please ensure the file is playable.'
        elif len(error_message) > 200:
            error_message = 'An error occurred while processing your file.'
        job_store.update(job_id, step="error", progress=0, error=error_message)

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"Cleaned up temporary file: {filepath}")


async def cleanup_expired_jobs():
    """Periodically remove jobs older than JOB_TTL_SECONDS."""
    while True:
        await asyncio.sleep(JOB_CLEANUP_INTERVAL)
        removed = job_store.remove_expired()
        if removed:
            logger.info(f"Cleaned up {removed} expired job(s)")
