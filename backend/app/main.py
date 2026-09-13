from fastapi import FastAPI

from app.core.config import settings
from app.core.errors import register_error_handlers
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import auth, bookings, catalog, operations

app = FastAPI(title=settings.APP_NAME)
register_error_handlers(app)
if settings.APP_ENV in {"development", "test"}:
    app.add_middleware(CORSMiddleware,
        allow_origins=[origin for origin in settings.DEV_CORS_ORIGINS if origin != "*"],
        allow_methods=["GET", "POST", "PATCH"], allow_headers=["Authorization", "Content-Type"])
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(bookings.router)
app.include_router(operations.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "procureflow-api"}
