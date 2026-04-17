import httpx

from app.core.config import settings


def build_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=settings.request_timeout_seconds)
