import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        start = time.time()
        response: Response = await call_next(request)
        latency_ms = (time.time() - start) * 1000
        log_payload = {
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "latency_ms": round(latency_ms, 2),
            "ticket_id": request.path_params.get("ticket_id")
        }
        logger.info(json.dumps(log_payload))
        response.headers["X-Correlation-ID"] = correlation_id
        return response
