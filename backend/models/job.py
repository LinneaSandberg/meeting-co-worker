import time

from config import JOB_TTL_SECONDS


class JobStore:
    """In-memory store for background processing jobs."""

    def __init__(self):
        self._jobs: dict[str, dict] = {}

    def create(self, job_id: str) -> dict:
        job = {"step": "uploading", "progress": 0, "created_at": time.time()}
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> dict | None:
        return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs):
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)

    def remove_expired(self) -> int:
        now = time.time()
        expired = [
            job_id for job_id, job in self._jobs.items()
            if now - job.get("created_at", now) > JOB_TTL_SECONDS
        ]
        for job_id in expired:
            del self._jobs[job_id]
        return len(expired)

    def __contains__(self, job_id: str) -> bool:
        return job_id in self._jobs


job_store = JobStore()
