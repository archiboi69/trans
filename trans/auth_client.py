from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
import re
import time
from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import SecretStr

from .dtos import TransErrorResponse, TransTokenResponse
from .config import TransSdkConfig
from .exceptions import TransAuthError, TransAuthRejectedError, TransApiUnreachableError, TransInvalidResponseError

logger = logging.getLogger("trans.auth")
_RAW_PREVIEW_MAX_LEN = 1200


def _redact_token_like_text(value: str) -> str:
    redacted = value
    redacted = " ".join(redacted.split())
    redacted = re.sub(
        r'(?i)("?(?:authorization|api[-_]?key|access[_-]?token|refresh[_-]?token|token)"?\s*[:=]\s*"?)([^",\s}]+)("?)',
        r"\1[REDACTED]\3",
        redacted,
    )
    redacted = re.sub(r"(?i)\bbearer\s+\S+", "Bearer [REDACTED]", redacted)
    return redacted


class TransAuthClient:
    def __init__(
        self,
        config: TransSdkConfig,
        client: httpx.AsyncClient | None = None,
    ):
        self._config = config
        self._client = client
        self._access_token: str | None = None
        self._expires_at: datetime | None = None
        self._refresh_token: str | None = None

    def set_refresh_token(self, refresh_token: str) -> None:
        self._refresh_token = refresh_token

    def current_refresh_token(self) -> str | None:
        # Refresh tokens can rotate; callers that persist tokens should re-save after usage.
        return self._refresh_token

    def current_access_token_expires_at(self) -> datetime | None:
        return self._expires_at

    async def get_access_token(self) -> str:
        if self._access_token and self._expires_at:
            if datetime.now(tz=timezone.utc) < self._expires_at:
                return self._access_token

        if self._refresh_token:
            token = await self._refresh_access_token(self._refresh_token)
        else:
            raise TransAuthError("Trans access token missing. Complete OAuth authorization first.")

        self._store_token(token)
        return self._access_token or ""

    def build_auth_url(self, redirect_uri: str, state: str | None = None) -> str:
        query = {
            "client_id": self._config.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
        }
        if state:
            query["state"] = state
        return f"{self._config.auth_base_url.rstrip('/')}/oauth2/auth?{urlencode(query)}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> TransTokenResponse:
        token = await self._request_token(code=code, redirect_uri=redirect_uri)
        self._store_token(token)
        return token

    async def auth_headers(self) -> dict[str, str]:
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Api-key": self._config.api_key,
        }

    async def _request_token(self, code: str, redirect_uri: str) -> TransTokenResponse:
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
        }
        return await self._post_token(payload)

    async def _refresh_access_token(self, refresh_token: str) -> TransTokenResponse:
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
        }
        return await self._post_token(payload)

    async def _post_token(self, payload: dict[str, str]) -> TransTokenResponse:
        # OAuth authorize UI lives on auth host, but token exchange is served
        # under the API host `/ext/auth-api/accounts/token`.
        url = f"{self._config.api_base_url.rstrip('/')}/ext/auth-api/accounts/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Api-key": self._config.api_key,
        }
        safe_payload = {
            key: ("[REDACTED]" if key in {"client_secret", "refresh_token", "code"} else value)
            for key, value in payload.items()
        }
        t0 = time.monotonic()

        try:
            if self._client:
                resp = await self._client.post(url, data=payload, headers=headers, timeout=30.0)
            else:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, data=payload, headers=headers, timeout=30.0)
        except httpx.RequestError as exc:
            elapsed_ms = (time.monotonic() - t0) * 1000
            logger.error(
                "Trans auth token request failed",
                extra={
                    "trans_auth_interaction": {
                        "method": "POST",
                        "url": url,
                        "request_body": safe_payload,
                        "elapsed_ms": round(elapsed_ms, 1),
                        "error": str(exc),
                    }
                },
            )
            raise TransApiUnreachableError("Trans API unreachable") from exc

        raw = resp.text
        elapsed_ms = (time.monotonic() - t0) * 1000
        response_payload: Any = None
        try:
            response_payload = resp.json()
        except Exception:
            response_payload = _redact_token_like_text(raw)[:_RAW_PREVIEW_MAX_LEN] if raw else None

        safe_response: Any = response_payload
        if isinstance(response_payload, dict):
            safe_response = {
                key: ("[REDACTED]" if "token" in key.lower() else value)
                for key, value in response_payload.items()
            }
        elif isinstance(response_payload, str):
            safe_response = _redact_token_like_text(response_payload)[:_RAW_PREVIEW_MAX_LEN]

        log_data = {
            "method": "POST",
            "url": url,
            "request_body": safe_payload,
            "status_code": resp.status_code,
            "response_headers": dict(resp.headers),
            "response_body": safe_response,
            "elapsed_ms": round(elapsed_ms, 1),
        }
        log_message = "Trans auth POST %s -> %s (%.0fms)"
        if resp.status_code >= 400:
            logger.error(
                log_message,
                url,
                resp.status_code,
                elapsed_ms,
                extra={"trans_auth_interaction": log_data},
            )
        else:
            logger.info(
                log_message,
                url,
                resp.status_code,
                elapsed_ms,
                extra={"trans_auth_interaction": log_data},
            )

        if resp.status_code >= 400:
            detail = self._error_detail(raw) or f"Trans API error ({resp.status_code})"
            if resp.status_code == 401:
                raise TransAuthRejectedError(detail)

            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {}

            if payload.get("error") == "invalid_grant":
                raise TransAuthRejectedError(detail)

            raise TransAuthRejectedError(detail)

        try:
            parsed = resp.json()
        except json.JSONDecodeError as exc:
            raise TransInvalidResponseError("Trans API invalid response") from exc

        return TransTokenResponse.model_validate(parsed)

    def _store_token(self, token: TransTokenResponse) -> None:
        self._access_token = token.access_token
        self._refresh_token = token.refresh_token
        self._expires_at = datetime.now(tz=timezone.utc) + timedelta(
            seconds=max(0, token.expires_in - 30)
        )

    def _error_detail(self, body: str) -> str | None:
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return None
        try:
            error = TransErrorResponse.model_validate(payload)
        except Exception:
            return None
        if error.error_description:
            return f"Trans API error: {error.error_description}"
        return f"Trans API error: {error.error}"
