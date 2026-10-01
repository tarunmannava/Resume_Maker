from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .api.queue_routes import queue_router
from .services.job_worker import start_worker, stop_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_worker()
    yield
    stop_worker()


app = FastAPI(
    title="Resume Rewriter API v2",
    description="ATS-focused LaTeX resume analysis, keyword scoring, and rewriting API.",
    version="0.2.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(queue_router, prefix="/api")
