from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import os
from pathlib import Path

from app.api import translate, history, youtube, settings as settings_api
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting YTT - Transcript Translator")
    print(f"LibreTranslate URL: {settings.LIBRETRANSLATE_URL}")
    print(f"Server running at http://{settings.APP_HOST}:{settings.APP_PORT}")
    print(f"API Documentation: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    yield
    print("Shutting down YTT")


app = FastAPI(
    title="YTT - Transcript Translator",
    version="1.0.0",
    description="Local web application for translating text and transcript files",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None  # Disable ReDoc due to CDN issues
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
        "version": "1.0.0"
    }


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
                    print(f"SPA Route: {path} -> serving index.html")
                    return await super().get_response("index.html", scope)
                else:
                    print(f"File not found: {path}")
            raise ex
        except Exception as ex:
            # Catch any other exceptions
            print(f"Error serving {path}: {ex}")
            raise ex


# Serve frontend static files if they exist
static_path = Path("./static")
if static_path.exists():
    # Mount SPA handler - must be last to catch all routes
    app.mount("/", SPAStaticFiles(directory="static", html=True), name="spa")