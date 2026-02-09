"""v1 API router registration."""

from fastapi import APIRouter

# Import individual endpoint modules
from src.api.v1 import auth

router = APIRouter(prefix="/v1")

# Register sub-routers
router.include_router(auth.router)
