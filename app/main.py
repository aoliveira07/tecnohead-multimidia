from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routes import router
from app.runtime import Runtime
from app.settings import load_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

settings = load_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime = Runtime(settings)
    app.state.runtime = runtime
    await runtime.start()
    try:
        yield
    finally:
        await runtime.stop()


app = FastAPI(
    title="TecnoHead Multimídia",
    version=__version__,
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)
app.include_router(router)

web_dir = Path(__file__).resolve().parents[1] / "web"
app.mount("/static", StaticFiles(directory=web_dir / "static"), name="static")


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(web_dir / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port)
