from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import json
import os
import logging
from pathlib import Path

from app.api import translate, history, youtube, settings as settings_api
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ytt")

# Load build info
BUILD_INFO_PATH = Path("./build-info.json")
BUILD_INFO = {"version": "1.0.0", "build_date": "dev", "git_commit": "dev"}
if BUILD_INFO_PATH.exists():
    try:
        BUILD_INFO = json.loads(BUILD_INFO_PATH.read_text())
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting YTT - Transcript Translator")
    logger.info(
        "Version: %s | Build: %s | Commit: %s",
        BUILD_INFO["version"],
        BUILD_INFO["build_date"],
        BUILD_INFO["git_commit"],
    )
    logger.info("LibreTranslate URL: %s", settings.LIBRETRANSLATE_URL)
    logger.info("Data directory: %s", settings.DATA_DIR.resolve())
    logger.info("Transcript directory: %s", settings.TRANSCRIPT_DIR.resolve())
    logger.info("Server running at http://%s:%s", settings.APP_HOST, settings.APP_PORT)
    logger.info(
        "API Documentation: http://%s:%s/docs", settings.APP_HOST, settings.APP_PORT
    )
    yield
    logger.info("Shutting down YTT")


app = FastAPI(
    title="YTT - Transcript Translator",
    version="1.0.0",
    description="Local web application for translating text and transcript files",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,  # Disable ReDoc due to CDN issues
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(translate.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(youtube.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "YTT",
        "version": BUILD_INFO["version"],
        "build_date": BUILD_INFO["build_date"],
        "git_commit": BUILD_INFO["git_commit"],
    }


@app.get("/api/version")
async def get_version():
    return BUILD_INFO


# Custom StaticFiles handler for SPA routing
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            # First try to serve the exact path
            response = await super().get_response(path, scope)
            return response
        except StarletteHTTPException as ex:
            if ex.status_code == 404:
                # For paths without file extensions (routes), serve index.html
                # This allows client-side routing to take over
                if not path or "." not in path.split("/")[-1]:
                    logger.debug("SPA Route: %s -> serving index.html", path)
                    return await super().get_response("index.html", scope)
                else:
                    logger.warning("File not found: %s", path)
            raise ex
        except Exception as ex:
            # Catch any other exceptions
            logger.error("Error serving %s: %s", path, ex)
            raise ex


# Serve frontend static files if they exist
static_path = Path("./static")
if static_path.exists():
    # Mount SPA handler - must be last to catch all routes
    app.mount("/", SPAStaticFiles(directory="static", html=True), name="spa")
