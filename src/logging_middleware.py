import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.time()
        correlation_id = str(uuid.uuid4())
        response = await call_next(request)
        latency = int((time.time() - start) * 1000)
        payload = {
            "correlation_id": correlation_id,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": latency,
        }
        logging.getLogger("uvicorn.access").info(json.dumps(payload))
        return response
