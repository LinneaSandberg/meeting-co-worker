import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.upload import router as upload_router
from routes.jobs import router as jobs_router
from routes.integrations import router as integrations_router
from services.job_service import cleanup_expired_jobs


@asynccontextmanager
async def lifespan(app):
    asyncio.create_task(cleanup_expired_jobs())
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(jobs_router)
app.include_router(integrations_router)


if __name__ == '__main__':
    import uvicorn

    print("\n" + "="*60)
    print("Meeting Copilot Web UI")
    print("="*60)
    print("\nOpen your browser to: http://localhost:5001")
    print("\nPress Ctrl+C to stop the server\n")

    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)
