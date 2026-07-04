from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import attendance, auth, employees, leave, uploads

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="HRMS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="static_uploads")

app.include_router(auth.router, prefix="/api")
app.include_router(employees.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(leave.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
