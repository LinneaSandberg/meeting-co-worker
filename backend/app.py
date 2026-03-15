import os
import uuid
import asyncio
from pathlib import Path
from functools import partial

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from transcribe import process_meeting
from integrations import (
    check_github_config,
    check_calendar_config,
    create_github_issue,
    format_action_item_issue,
    format_question_issue,
    create_calendar_event,
    format_question_event
)
from logging_config import get_app_logger

# Initialize logger
logger = get_app_logger()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'mp4', 'avi', 'mov'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory job tracking
jobs: dict[str, dict] = {}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


async def run_job(job_id: str, filepath: str):
    """Run the transcription + extraction pipeline in a background thread."""
    try:
        def on_progress(step: str):
            if step == "transcribing":
                jobs[job_id].update(step="transcribing", progress=33)
            elif step == "extracting":
                jobs[job_id].update(step="extracting", progress=66)
            elif step == "complete":
                jobs[job_id].update(step="complete", progress=100)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(process_meeting, filepath, on_progress=on_progress)
        )

        jobs[job_id].update(
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
        jobs[job_id].update(step="error", progress=0, error=error_message)

    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug(f"Cleaned up temporary file: {filepath}")


@app.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload and start async processing."""
    logger.info("Received file upload request")

    if not file.filename:
        raise HTTPException(status_code=400, detail='No file selected')

    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        )

    try:
        # Save uploaded file
        import re
        filename = re.sub(r'[^\w\s\-.]', '', file.filename).strip()
        if not filename:
            filename = 'upload'
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail='File too large. Maximum size is 100MB.')

        with open(filepath, 'wb') as f:
            f.write(content)

        logger.info(f"File saved: {filename} ({len(content)} bytes)")

        # Create job and start processing
        job_id = str(uuid.uuid4())
        jobs[job_id] = {"step": "uploading", "progress": 0}

        asyncio.create_task(run_job(job_id, filepath))

        return {"job_id": job_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling file upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail='Failed to process upload')


@app.get('/jobs/{job_id}/stream')
async def job_stream(job_id: str, request: Request):
    """SSE endpoint for streaming job progress."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail='Job not found')

    import json

    async def event_generator():
        last_step = None
        while True:
            if await request.is_disconnected():
                break

            job = jobs.get(job_id)
            if not job:
                break

            current_step = job.get("step")

            if current_step != last_step:
                last_step = current_step
                data = {"step": job["step"], "progress": job["progress"]}

                if current_step == "complete" and "result" in job:
                    data["result"] = job["result"]
                    yield {"event": "message", "data": json.dumps(data)}
                    break
                elif current_step == "error":
                    data["error"] = job.get("error", "Unknown error")
                    yield {"event": "message", "data": json.dumps(data)}
                    break
                else:
                    yield {"event": "message", "data": json.dumps(data)}

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.get('/jobs/{job_id}/result')
async def job_result(job_id: str):
    """Get the final result for a completed job (fallback for SSE)."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail='Job not found')

    job = jobs[job_id]

    if job["step"] == "error":
        raise HTTPException(status_code=500, detail=job.get("error", "Processing failed"))

    if job["step"] != "complete":
        return {"status": "processing", "step": job["step"], "progress": job["progress"]}

    return job["result"]


@app.get('/integration-status')
async def integration_status():
    """Check which integrations are configured and available."""
    logger.debug("Checking integration status")

    github_config = check_github_config()
    calendar_config = check_calendar_config()

    logger.info(f"Integration status - GitHub: {github_config['enabled']}, Calendar: {calendar_config['enabled']}")

    return {
        'github_enabled': github_config['enabled'],
        'github_repo': github_config.get('repo'),
        'calendar_enabled': calendar_config['enabled'],
        'calendar_type': calendar_config.get('calendar_type')
    }


@app.post('/create-integrations')
async def create_integrations(request: Request):
    """Handle creation of GitHub issues and Google Calendar events."""
    logger.info("Received create-integrations request")

    data = await request.json()

    if not data:
        raise HTTPException(status_code=400, detail='No data provided')

    action_items = data.get('action_items', [])
    open_questions = data.get('open_questions', [])
    logger.info(f"Processing {len(action_items)} action items, {len(open_questions)} questions")

    results = {
        'github_issues': [],
        'calendar_events': []
    }

    # Process action items
    for item in action_items:
        if item.get('create_github'):
            title, body = format_action_item_issue(
                task=item['task'],
                owner=item.get('owner'),
                deadline=item.get('deadline')
            )

            result = create_github_issue(title, body, issue_type="action_item")

            results['github_issues'].append({
                'type': 'action_item',
                'title': item['task'],
                'url': result.get('issue_url'),
                'issue_number': result.get('issue_number'),
                'error': result.get('error')
            })

    # Process open questions
    for question in open_questions:
        if question.get('create_github'):
            title, body = format_question_issue(
                question=question['question'],
                context=question.get('context')
            )

            result = create_github_issue(title, body, issue_type="open_question")

            results['github_issues'].append({
                'type': 'open_question',
                'title': question['question'],
                'url': result.get('issue_url'),
                'issue_number': result.get('issue_number'),
                'error': result.get('error')
            })

        if question.get('create_calendar'):
            summary, description, attendees = format_question_event(
                question=question['question'],
                context=question.get('context')
            )

            duration = int(os.getenv('DEFAULT_MEETING_DURATION', 30))

            result = create_calendar_event(
                summary=summary,
                description=description,
                attendees=attendees,
                duration_minutes=duration
            )

            results['calendar_events'].append({
                'type': 'open_question',
                'title': question['question'],
                'url': result.get('event_url'),
                'event_id': result.get('event_id'),
                'attendees': attendees,
                'error': result.get('error')
            })

    any_success = (
        any(item.get('url') for item in results['github_issues']) or
        any(event.get('url') for event in results['calendar_events'])
    )

    github_success = sum(1 for item in results['github_issues'] if item.get('url'))
    github_failed = len(results['github_issues']) - github_success
    calendar_success = sum(1 for event in results['calendar_events'] if event.get('url'))
    calendar_failed = len(results['calendar_events']) - calendar_success

    logger.info(
        f"Integration results - GitHub: {github_success} created, {github_failed} failed; "
        f"Calendar: {calendar_success} created, {calendar_failed} failed"
    )

    return {
        'success': any_success,
        'results': results
    }


if __name__ == '__main__':
    import uvicorn

    print("\n" + "="*60)
    print("Meeting Copilot Web UI")
    print("="*60)
    print("\nOpen your browser to: http://localhost:5001")
    print("\nPress Ctrl+C to stop the server\n")

    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)
