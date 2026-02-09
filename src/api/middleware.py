"""API middleware for correlation ID tracking."""

import uuid
from typing import Callable

from fastapi import Request, Response


async def correlation_id_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to handle correlation IDs for request tracking.

    - Accepts X-Request-ID header from client
    - Generates UUID if not provided
    - Returns in response headers
    - Stores in request.state for use in logs
    """
    # Get correlation ID from header or generate new one
    correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    # Store in request state for access in endpoints
    request.state.correlation_id = correlation_id

    # Process request
    response = await call_next(request)

    # Return correlation ID in response headers
    response.headers["X-Request-ID"] = correlation_id

    return response
