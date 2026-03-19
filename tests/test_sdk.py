import pytest
import httpx
from trans import TransApiClient, TransAuthClient, TransSdkConfig, TransApiError

@pytest.fixture
def config():
    return TransSdkConfig(
        api_key="test_key",
        client_id="test_client",
        client_secret="test_secret",
    )

@pytest.mark.asyncio
async def test_api_client_error_handling(config):
    def handler(request):
        return httpx.Response(400, json={"message": "Bad Request", "detail": "Test error"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api_client = TransApiClient(config=config, client=client)
        with pytest.raises(TransApiError) as excinfo:
            await api_client._execute_request("GET", "test")
        
        assert excinfo.value.normalized.status_code == 400
        assert excinfo.value.normalized.detail == "Test error"

@pytest.mark.asyncio
async def test_auth_client_url_build(config):
    auth_client = TransAuthClient(config=config)
    url = auth_client.build_auth_url("https://callback.test")
    assert "client_id=test_client" in url
    assert "redirect_uri=https%3A%2F%2Fcallback.test" in url
