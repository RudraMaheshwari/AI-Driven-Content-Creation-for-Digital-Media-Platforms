"""FastAPI application entrypoint.

Run:
    python app.py                  # uses settings.app_host / app_port
    uvicorn app:app --reload       # during development
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import generate, health, refine
from src.config.settings import settings
from src.database.init_db import init_database
from src.utils.exceptions import AppError
from src.utils.logger import get_logger

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"starting {settings.app_name} env={settings.app_env}")
    init_database()
    yield
    logger.info("shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):  # noqa: ARG001
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message},
        )

    # Serve generated images back to the frontend.
    images_dir = Path(settings.image_storage_dir).resolve()
    images_dir.mkdir(parents=True, exist_ok=True)
    app.mount(
        settings.public_image_base_url,
        StaticFiles(directory=str(images_dir)),
        name="images",
    )

    app.include_router(health.router)
    app.include_router(generate.router)
    app.include_router(refine.router)

    @app.get("/", tags=["meta"])
    def root():
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
        }

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
