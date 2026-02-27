"""GET /health — health check for load balancers & monitoring."""

from fastapi import APIRouter

from src.api.dependencies import get_config, get_current_provider_info

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Basic health check — always returns 200 if the server is running."""
    return {"status": "ok"}


@router.get("/info")
async def app_info() -> dict:
    """App version and configuration summary."""
    config = get_config()
    provider_info = get_current_provider_info()
    return {
        "name": config.get("app", {}).get("name", "DeutschLerner"),
        "version": config.get("app", {}).get("version", "1.0.0"),
        "ai_provider": provider_info,
        "difficulty": config.get("learning", {}).get("difficulty", "A2"),
    }
