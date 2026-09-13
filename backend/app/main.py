from fastapi import FastAPI

from app.core.config import settings
from app.core.errors import register_error_handlers

app = FastAPI(title=settings.APP_NAME)
register_error_handlers(app)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "procureflow-api"}
