import re

with open("trans_client/api_client.py", "r") as f:
    content = f.read()

# Update init of TransApiClient to take base_url and rate_limit directly
content = re.sub(
    r"def __init__\(self, client: httpx\.AsyncClient \| None = None\):.*?(?=    async def get_freight_details)",
    """def __init__(
        self, 
        base_url: str = "https://api.platform.trans.eu/ext/", 
        rate_limit: int = 5,
        client: httpx.AsyncClient | None = None
    ):
        self._base_url = base_url
        self._rate_limit = rate_limit
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
        request_body: dict | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        url = f"{self._base_url.rstrip('/')}/{path.lstrip('/')}"
        
        await _acquire_trans_api_slot(self._rate_limit)

        start_time = time.monotonic()
        try:
            resp = await self._client.request(
                method,
                url,
                json=request_body,
                timeout=timeout,
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
                normalized = _normalize_error(resp)
                raise TransApiError(normalized)
                
            return resp.json()
            
        except httpx.RequestError as exc:
            raise TransApiUnreachableError(str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise Exception("Trans API invalid JSON response") from exc

""",
    content,
    flags=re.DOTALL | re.MULTILINE
)

with open("trans_client/api_client.py", "w") as f:
    f.write(content)
