"""GET /providers, PUT /provider — AI provider management."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.ai.factory import list_providers
from src.api.dependencies import get_current_provider_info, set_ai_provider

router = APIRouter()


class SwitchProviderRequest(BaseModel):
    """Request body for switching AI provider."""

    provider: str
    model: str | None = None


@router.get("/providers")
async def list_available_providers() -> dict:
    """List all available AI providers and their configuration status."""
    return {"providers": list_providers()}


@router.get("/provider/current")
async def get_current_provider() -> dict:
    """Get the currently active AI provider."""
    return get_current_provider_info()


@router.put("/provider")
async def switch_provider(body: SwitchProviderRequest) -> dict:
    """Switch the active AI provider."""
    try:
        provider = set_ai_provider(body.provider, body.model)
        return {
            "provider": provider.name,
            "model": body.model,
            "status": "switched",
        }
    except (ValueError, RuntimeError) as e:
        return {"error": str(e)}
