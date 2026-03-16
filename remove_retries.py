import re

with open("trans_client/api_client.py", "r") as f:
    content = f.read()

# Remove the retry loops, keeping just the core execution. 
# This requires a bit of parsing since python relies on indentation.
# We will just replace the execute_with_retry method with a straight execution method.

new_execute_method = """    async def _execute_request(
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
"""

# Find the start of _execute_with_retries and replace it up to get_freight_details
# This relies on the file structure of api_client.py
content = re.sub(
    r"    async def _execute_with_retries\(.*?(?=    async def get_freight_details)",
    new_execute_method,
    content,
    flags=re.DOTALL | re.MULTILINE
)

# Also need to replace calls to _execute_with_retries with _execute_request
content = content.replace("self._execute_with_retries(", "self._execute_request(")
# Remove retry_count kwargs from error instantiations
content = re.sub(r", \*, retry_count: int = 0", "", content)
content = re.sub(r"self\.retry_count = retry_count\n\s+", "", content)
content = re.sub(r"\(retry_count=retry_count\)", "()", content)

with open("trans_client/api_client.py", "w") as f:
    f.write(content)
