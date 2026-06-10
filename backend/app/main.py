from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

app = FastAPI(
    title="Resume Rewriter API v2",
    description="ATS-focused LaTeX resume analysis, keyword scoring, and rewriting API.",
    version="0.2.0",
)
print("DEBUG: LOADED MAIN.PY FROM D:\\Projects\\Resume Maker\\backend\\app\\main.py", flush=True)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
