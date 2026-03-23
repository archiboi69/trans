from __future__ import annotations

from typing import Any

import structlog
from structlog.contextvars import bound_contextvars, get_contextvars

def bind_observability_context(**fields: Any):
    return bound_contextvars(**fields)


def current_observability_context() -> dict[str, Any]:
    return dict(get_contextvars())


def log_sdk_event(
    logger_name: str,
    *,
    operation: str,
    method: str,
    url: str,
    duration_ms: float,
    status_code: int | None = None,
    retry_after_seconds: float | None = None,
    provider_request_id: str | None = None,
    request_body: Any = None,
    response_body: Any = None,
    response_headers: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
    **extra: Any,
) -> None:
    event: dict[str, Any] = {
        "kind": "sdk_event",
        "sdk": "trans",
        "operation": operation,
        "method": method,
        "url": url,
        "duration_ms": round(duration_ms, 1),
        **current_observability_context(),
        **extra,
    }
    if status_code is not None:
        event["status_code"] = status_code
    if retry_after_seconds is not None:
        event["retry_after_seconds"] = retry_after_seconds
    if provider_request_id is not None:
        event["provider_request_id"] = provider_request_id
    if request_body is not None:
        event["request_body"] = request_body
    if response_body is not None:
        event["response_body"] = response_body
    if response_headers is not None:
        event["response_headers"] = response_headers
    if error is not None:
        event["error"] = error

    logger = structlog.get_logger(logger_name)
    if error is not None or (status_code is not None and status_code >= 400):
        logger.error("sdk_event", **event)
        return
    logger.info("sdk_event", **event)
