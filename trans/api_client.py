from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import logging
import random
import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx


from .dtos import (    TransFreightExchangeRequest,
    TransBulkCancelPublicationResponse,
    TransFreightExchangeResponse,
)
from .config import TransSdkConfig
from .exceptions import TransApiError, TransApiUnreachableError, TransInvalidResponseError

_RAW_PREVIEW_MAX_LEN = 1200
_RAW_TEXT_REDACTION_SCAN_MAX = _RAW_PREVIEW_MAX_LEN * 4
_VALIDATION_SUMMARY_LIMIT = 5

logger = logging.getLogger("trans.api")


@dataclass(frozen=True)
class TransNormalizedError:
    status_code: int
    detail: str | None
    title: str | None
    provider_response_id: str | None
    validation_messages_flat: tuple[tuple[str, str], ...]
    raw_preview: str | None
    retry_after_seconds: float | None


class TransApiClient:
    def __init__(
        self,
        config: TransSdkConfig,
        client: httpx.AsyncClient | None = None,
    ):
        self._config = config
        if client:
            self._client = client
            self._owns_client = False
        else:
            self._client = httpx.AsyncClient()
            self._owns_client = True

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _execute_request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        request_body: dict | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        url = f"{self._config.api_base_url.rstrip('/')}/{path.lstrip('/')}"
        
        

        start_time = time.monotonic()
        try:
            resp = await self._client.request(
                method,
                url,
                json=request_body,
                headers=headers,
                timeout=timeout or self._config.timeout_seconds,
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000
            
            _log_interaction(
                method=method,
                url=url,
                request_body=request_body,
                resp=resp,
                elapsed_ms=elapsed_ms,
            )
            
            if resp.status_code >= 400:
                normalized = _normalize_trans_error(resp)
                raise TransApiError(normalized)
                
            return resp
            
        except httpx.RequestError as exc:
            raise TransApiUnreachableError(str(exc)) from exc

    async def new_freight_to_freight_exchange(
        self,
        payload: TransFreightExchangeRequest,
        *,
        access_token: str,
    ) -> TransFreightExchangeResponse:
        path = "ext/freights-api/v1/freight-exchange"
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Api-key": self._config.api_key,
        }
        body = payload.model_dump(by_alias=True, exclude_none=True)
        resp = await self._execute_request(
            method="POST",
            path=path,
            headers=headers,
            request_body=body,
        )

        try:
            parsed = resp.json()
        except json.JSONDecodeError as exc:
            raise TransInvalidResponseError("Trans API invalid JSON response") from exc
        return TransFreightExchangeResponse.model_validate(parsed)

    async def refresh_freight_publication(
        self,
        *,
        freight_id: int,
        access_token: str,
    ) -> None:
        """
        Refresh freight publication.
        """
        path = f"ext/freights-api/v1/freights/{freight_id}/refresh_publication"
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Api-key": self._config.api_key,
        }
        await self._execute_request(
            method="PUT",
            path=path,
            headers=headers,
        )

    async def cancel_freight_publication(self, *, freight_id: int, access_token: str) -> None:
        """
        Cancel freight publication.
        """
        path = f"ext/freights-api/v1/cancelPublication/{freight_id}"
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Api-key": self._config.api_key,
        }
        await self._execute_request(
            method="POST",
            path=path,
            headers=headers,
        )

    async def bulk_cancel_freight_publications(
        self, *, freight_ids: list[int], access_token: str
    ) -> TransBulkCancelPublicationResponse:
        path = "ext/freights-api/v1/cancelPublication"
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Api-key": self._config.api_key,
        }
        resp = await self._execute_request(
            method="POST",
            path=path,
            headers=headers,
            request_body=freight_ids,
        )

        try:
            parsed = resp.json()
        except json.JSONDecodeError as exc:
            raise TransInvalidResponseError("Trans API invalid JSON response") from exc
        return TransBulkCancelPublicationResponse.model_validate(parsed)




def _log_interaction(
    *,
    method: str,
    url: str,
    request_body: dict | None,
    resp: httpx.Response,
    elapsed_ms: float,
) -> None:
    safe_body = _redact_json_value(request_body) if request_body else None

    safe_response: Any = None
    try:
        response_body = resp.json()
        safe_response = (
            _redact_json_value(response_body)
            if isinstance(response_body, (dict, list))
            else response_body
        )
    except Exception:
        raw_text = resp.text or ""
        if raw_text:
            safe_response = _truncate(
                _redact_text(_compact_single_line(raw_text)),
                max_len=_RAW_PREVIEW_MAX_LEN,
            )

    data = {
        "method": method,
        "url": url,
        "request_body": safe_body,
        "status_code": resp.status_code,
        "response_headers": dict(resp.headers),
        "response_body": safe_response,
        "elapsed_ms": round(elapsed_ms, 1),
    }

    log_message = "Trans API %s %s -> %s (%.0fms)"
    if resp.status_code >= 400:
        logger.error(
            log_message,
            method,
            url,
            resp.status_code,
            elapsed_ms,
            extra={"trans_interaction": data},
        )
        return

    logger.info(
        log_message,
        method,
        url,
        resp.status_code,
        elapsed_ms,
        extra={"trans_interaction": data},
    )


def _extract_trans_error(resp: httpx.Response) -> str:
    return _format_trans_error(_normalize_trans_error(resp))


def _normalize_trans_error(resp: httpx.Response) -> TransNormalizedError:
    raw = resp.text or ""
    try:
        payload = resp.json()
    except Exception:
        payload = None

    envelope, provider_response_id = _extract_envelope(payload)
    validation_messages_flat = _flatten_validation_messages(
        envelope.get("validation_messages") if isinstance(envelope, dict) else None
    )

    detail = _first_non_blank(
        _as_non_blank_str(envelope.get("detail")) if isinstance(envelope, dict) else None,
        _as_non_blank_str(envelope.get("message")) if isinstance(envelope, dict) else None,
        _as_non_blank_str(envelope.get("error_description"))
        if isinstance(envelope, dict)
        else None,
        _as_non_blank_str(envelope.get("error")) if isinstance(envelope, dict) else None,
    )

    title = _as_non_blank_str(envelope.get("title")) if isinstance(envelope, dict) else None
    upstream_status = _coerce_int(envelope.get("status")) if isinstance(envelope, dict) else None
    raw_preview = _build_raw_preview(raw=raw, payload=payload)
    retry_after_seconds = _parse_retry_after(resp.headers.get("Retry-After"))

    return TransNormalizedError(
        status_code=upstream_status or resp.status_code,
        detail=detail,
        title=title,
        provider_response_id=provider_response_id,
        validation_messages_flat=validation_messages_flat,
        raw_preview=raw_preview,
        retry_after_seconds=retry_after_seconds,
    )


def _parse_retry_after(value: str | None) -> float | None:
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    try:
        parsed_seconds = float(normalized)
    except ValueError:
        parsed_seconds = None

    if parsed_seconds is not None:
        return max(parsed_seconds, 0.0)

    try:
        parsed_dt = parsedate_to_datetime(normalized)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None

    if parsed_dt.tzinfo is None:
        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
    delta = (parsed_dt.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds()
    return max(delta, 0.0)


def _extract_envelope(payload: Any) -> tuple[dict[str, Any], str | None]:
    if not isinstance(payload, dict):
        return {}, None

    provider_response_id = _as_non_blank_str(payload.get("id"))
    message = payload.get("message")
    if isinstance(message, dict):
        return message, provider_response_id
    return payload, provider_response_id


def _format_trans_error(normalized: TransNormalizedError) -> str:
    base = f"Trans API error ({normalized.status_code})"
    parts: list[str] = []

    if normalized.detail:
        parts.append(normalized.detail)
    elif normalized.title:
        parts.append(normalized.title)

    if normalized.validation_messages_flat:
        summary = "; ".join(
            f"{key}: {value}"
            for key, value in normalized.validation_messages_flat[:_VALIDATION_SUMMARY_LIMIT]
        )
        parts.append(summary)

    if not parts and normalized.raw_preview:
        parts.append(normalized.raw_preview)

    if not parts:
        return base
    return f"{base}: {' | '.join(parts)}"


def _flatten_validation_messages(value: Any) -> tuple[tuple[str, str], ...]:
    flattened: list[tuple[str, str]] = []

    def _visit(node: Any, *, path: str) -> None:
        if isinstance(node, dict):
            for key in sorted(node):
                key_text = str(key).strip()
                if not key_text:
                    continue
                next_path = f"{path}.{key_text}" if path else key_text
                _visit(node[key], path=next_path)
            return

        if isinstance(node, list):
            for idx, item in enumerate(node):
                next_path = f"{path}[{idx}]" if path else f"[{idx}]"
                _visit(item, path=next_path)
            return

        text = _as_non_blank_str(node)
        if text and path:
            flattened.append((path, text))

    if isinstance(value, dict):
        _visit(value, path="")
    elif value is not None:
        _visit(value, path="validation_messages")

    return tuple(flattened)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return (
        "token" in normalized
        or "authorization" in normalized
        or normalized in {"api_key", "apikey"}
    )


def _redact_json_value(value: Any, *, parent_key: str | None = None) -> Any:
    if parent_key and _is_sensitive_key(parent_key):
        return "[REDACTED]"

    if isinstance(value, dict):
        return {
            str(key): _redact_json_value(item, parent_key=str(key)) for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_json_value(item, parent_key=parent_key) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _redact_text(value: str) -> str:
    redacted = value
    redacted = re.sub(
        r'(?i)("?(?:authorization|api[-_]?key|access[_-]?token|refresh[_-]?token|token)"?\s*:\s*")([^"]+)(")',
        r"\1[REDACTED]\3",
        redacted,
    )
    redacted = re.sub(r"(?i)\bbearer\s+\S+", "Bearer [REDACTED]", redacted)
    redacted = re.sub(
        r"(?i)\b(authorization|api[-_]?key|access[_-]?token|refresh[_-]?token|token)\s*[:=]\s*(?:bearer\s+)?\S+",
        lambda match: f"{match.group(1)}=[REDACTED]",
        redacted,
    )
    return redacted


def _truncate(value: str, *, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[:max_len]


def _compact_single_line(value: str) -> str:
    # Keep raw previews log-friendly and bounded to one line.
    return " ".join(value.split())


def _build_raw_preview(*, raw: str, payload: Any) -> str | None:
    candidate = ""
    if isinstance(payload, (dict, list)):
        candidate = json.dumps(
            _redact_json_value(payload),
            ensure_ascii=True,
            separators=(",", ":"),
            default=str,
        )
    else:
        bounded_raw = _truncate(raw, max_len=_RAW_TEXT_REDACTION_SCAN_MAX).strip()
        compact_raw = _compact_single_line(bounded_raw)
        candidate = _redact_text(compact_raw)

    if not candidate:
        return None
    return _truncate(candidate, max_len=_RAW_PREVIEW_MAX_LEN)


def _coerce_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_non_blank_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_non_blank(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None
