import json
import asyncio

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from models.job import job_store

router = APIRouter()


@router.get('/jobs/{job_id}/stream')
async def job_stream(job_id: str, request: Request):
    """SSE endpoint for streaming job progress."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail='Job not found')

    async def event_generator():
        last_step = None
        while True:
            if await request.is_disconnected():
                break

            job = job_store.get(job_id)
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


@router.get('/jobs/{job_id}/result')
async def job_result(job_id: str):
    """Get the final result for a completed job (fallback for SSE)."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail='Job not found')

    job = job_store.get(job_id)

    if job["step"] == "error":
        raise HTTPException(status_code=500, detail=job.get("error", "Processing failed"))

    if job["step"] != "complete":
        return {"status": "processing", "step": job["step"], "progress": job["progress"]}

    return job["result"]
