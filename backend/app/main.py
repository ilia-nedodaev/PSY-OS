from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.routers import auth, clients, homework, messages, notes, payments, profile, sessions, sos, timeline


async def init_extensions():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception:
            pass
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_extensions()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="PSY OS — psychologist operating system API",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(clients.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(timeline.router, prefix="/api/v1")
app.include_router(notes.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(homework.router, prefix="/api/v1")
app.include_router(sos.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "ai_enabled": settings.ai_enabled,
        "version": "0.1.0",
    }


if settings.serve_frontend:
    frontend_path = (Path(__file__).resolve().parents[2] / "frontend").resolve()
    if not frontend_path.exists():
        frontend_path = (Path(__file__).resolve().parents[2]).resolve()
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
