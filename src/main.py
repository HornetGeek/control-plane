"""Control Plane - Multi-tenant SaaS Control Plane API."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.middleware import correlation_id_middleware
from src.api.v1 import router as v1_router
from src.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management."""
    # Startup
    settings = get_settings()
    app.state.settings = settings
    print(f"Starting Control Plane API in {settings.control_plane_env} mode")
    yield
    # Shutdown
    print("Shutting down Control Plane API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Control Plane API",
        description="Multi-tenant SaaS control plane for organization, tenant, and subscription management",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Middleware
    app.middleware("http")(correlation_id_middleware)

    # Exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "code": "INVALID_VALUE",
                "message": str(exc),
                "request_id": request.state.correlation_id,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle general exceptions."""
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "request_id": request.state.correlation_id,
            },
        )

    # Health endpoints
    @app.get("/health")
    async def health_check():
        """Liveness probe - simple health check."""
        return {"status": "healthy"}

    @app.get("/ready")
    async def readiness_check():
        """Readiness probe - check if service is ready to accept traffic."""
        # TODO: Add database connectivity check
        return {"status": "ready"}

    # API v1 routes
    app.include_router(v1_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
