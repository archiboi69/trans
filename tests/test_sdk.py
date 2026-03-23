import json
from contextlib import nullcontext

import httpx
import pytest
from structlog.testing import capture_logs
from trans import (
    TransApiClient,
    TransAuthClient,
    TransBulkCancelPublicationResponse,
    TransSdkConfig,
    TransApiError,
    TransAuthRejectedError,
    TransApiUnreachableError,
    TransFreightExchangeRequest,
    bind_observability_context,
)
from trans.dtos import (
    TransPayment,
    TransPaymentCurrency,
    TransPaymentPeriod,
    TransPaymentPeriodEnum,
    TransPaymentPrice,
)

@pytest.fixture
def config():
    return TransSdkConfig(
        api_key="test_key",
        client_id="test_client",
        client_secret="test_secret",
    )


def test_bind_observability_context_includes_correlation_fields() -> None:
    with capture_logs() as logs:
        with bind_observability_context(request_id="req-123", operation_id="op-456"):
            from trans.observability import log_sdk_event

            log_sdk_event(
                "sdk.trans.http",
                operation="publish_freight_offer",
                method="POST",
                url="https://api.test/freights",
                status_code=201,
                duration_ms=12.5,
            )

    assert logs[0]["request_id"] == "req-123"
    assert logs[0]["operation_id"] == "op-456"
    assert logs[0]["kind"] == "sdk_event"
    assert logs[0]["sdk"] == "trans"

@pytest.mark.asyncio
async def test_api_client_error_handling(config):
    def handler(request):
        return httpx.Response(400, json={"message": "Bad Request", "detail": "Test error"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api_client = TransApiClient(config=config, client=client)
        with capture_logs() as logs:
            with pytest.raises(TransApiError) as excinfo:
                await api_client._execute_request("test_request", "GET", "test")
        
        assert excinfo.value.normalized.status_code == 400
        assert excinfo.value.normalized.detail == "Test error"
        assert logs[0]["operation"] == "test_request"
        assert logs[0]["kind"] == "sdk_event"
        assert logs[0]["status_code"] == 400
        assert logs[0]["error"]["retryable"] is False

@pytest.mark.asyncio
async def test_auth_client_url_build(config):
    auth_client = TransAuthClient(config=config)
    url = auth_client.build_auth_url("https://callback.test")
    assert "client_id=test_client" in url
    assert "redirect_uri=https%3A%2F%2Fcallback.test" in url

@pytest.mark.asyncio
async def test_auth_client_exchange_code(config):
    def handler(request):
        return httpx.Response(200, json={
            "access_token": "abc",
            "refresh_token": "def",
            "expires_in": 3600,
            "token_type": "Bearer"
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        auth_client = TransAuthClient(config=config, client=client)
        token = await auth_client.exchange_code_for_token("code", "https://callback.test")
        assert token.access_token == "abc"
        assert token.refresh_token == "def"

@pytest.mark.asyncio
async def test_auth_client_rejection(config):
    def handler(request):
        return httpx.Response(401, json={"error": "invalid_grant", "error_description": "Invalid code"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        auth_client = TransAuthClient(config=config, client=client)
        with pytest.raises(TransAuthRejectedError):
            await auth_client.exchange_code_for_token("bad_code", "https://callback.test")

@pytest.mark.asyncio
async def test_api_client_publish_success(config):
    def handler(request):
        return httpx.Response(201, json={"id": 123, "status": "published"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api_client = TransApiClient(config=config, client=client)
        # Mock payload with required fields
        payload = TransFreightExchangeRequest(
            capacity=24.0,
            requirements={
                "is_ftl": True,
                "required_truck_bodies": ["truck"]
            },
            publish=True,
            spots=[
                {
                    "spot_order": 1,
                    "place": {
                        "address": {
                            "country": "pl",
                            "locality": "Wroclaw",
                            "postal_code": "50-001"
                        }
                    },
                    "operations": [
                        {
                            "operation_order": 1,
                            "type": "loading",
                            "timespans": {
                                "begin": "2026-03-20T10:00:00Z",
                                "end": "2026-03-20T12:00:00Z"
                            }
                        }
                    ]
                },
                {
                    "spot_order": 2,
                    "place": {
                        "address": {
                            "country": "de",
                            "locality": "Berlin",
                            "postal_code": "10115"
                        }
                    },
                    "operations": [
                        {
                            "operation_order": 1,
                            "type": "unloading",
                            "timespans": {
                                "begin": "2026-03-21T10:00:00Z",
                                "end": "2026-03-21T12:00:00Z"
                            }
                        }
                    ]
                }
            ]
        )
        response = await api_client.new_freight_to_freight_exchange(payload, access_token="token")
        assert response.id == 123


@pytest.mark.asyncio
async def test_api_client_publish_nests_payment_period_under_price(config):
    def handler(request):
        body = json.loads(request.content)
        assert body["payment"] == {
            "price": {
                "value": 999.0,
                "currency": "eur",
                "period": {
                    "payment": "deferred",
                    "days": 21,
                },
            }
        }
        return httpx.Response(201, json={"id": 123, "status": "published"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api_client = TransApiClient(config=config, client=client)
        payload = TransFreightExchangeRequest(
            capacity=24.0,
            requirements={
                "is_ftl": True,
                "required_truck_bodies": ["truck"],
            },
            payment=TransPayment(
                price=TransPaymentPrice(
                    value=999.0,
                    currency=TransPaymentCurrency.EUR,
                    period=TransPaymentPeriod(
                        payment=TransPaymentPeriodEnum.DEFERRED,
                        days=21,
                    ),
                ),
            ),
            publish=True,
            spots=[
                {
                    "spot_order": 1,
                    "place": {
                        "address": {
                            "country": "pl",
                            "locality": "Wroclaw",
                            "postal_code": "50-001",
                        }
                    },
                    "operations": [
                        {
                            "operation_order": 1,
                            "type": "loading",
                            "timespans": {
                                "begin": "2026-03-20T10:00:00Z",
                                "end": "2026-03-20T12:00:00Z",
                            },
                        }
                    ],
                }
            ],
        )

        response = await api_client.new_freight_to_freight_exchange(payload, access_token="token")

    assert response.id == 123

@pytest.mark.asyncio
async def test_api_client_429_retry_after(config):
    def handler(request):
        return httpx.Response(429, headers={"Retry-After": "10"}, json={"detail": "Too many requests"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api_client = TransApiClient(config=config, client=client)
        with pytest.raises(TransApiError) as excinfo:
            await api_client._execute_request("test_request", "GET", "test")
        
        assert excinfo.value.normalized.status_code == 429
        assert excinfo.value.normalized.retry_after_seconds == 10.0

@pytest.mark.asyncio
async def test_api_client_500_error(config):
    def handler(request):
        return httpx.Response(500, content=b"Internal Server Error")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api_client = TransApiClient(config=config, client=client)
        with pytest.raises(TransApiError) as excinfo:
            await api_client._execute_request("test_request", "GET", "test")
        
        assert excinfo.value.normalized.status_code == 500

@pytest.mark.asyncio
async def test_api_client_network_failure(config):
    def handler(request):
        raise httpx.ConnectError("Connection failed")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api_client = TransApiClient(config=config, client=client)
        with pytest.raises(TransApiUnreachableError):
            await api_client._execute_request("test_request", "GET", "test")

@pytest.mark.asyncio
async def test_api_client_refresh_cancel(config):
    def handler(request):
        if request.method == "PUT": # Refresh
            return httpx.Response(200, json={})
        if request.method == "POST": # Cancel
            return httpx.Response(201, json={})
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api_client = TransApiClient(config=config, client=client)
        # Should not raise
        await api_client.refresh_freight_publication(freight_id=123, access_token="token")
        await api_client.cancel_freight_publication(freight_id=123, access_token="token")


@pytest.mark.asyncio
async def test_api_client_bulk_cancel_success(config):
    def handler(request):
        assert request.method == "POST"
        assert request.url.path.endswith("/ext/freights-api/v1/cancelPublication")
        assert json.loads(request.content) == [856796, 234578]
        return httpx.Response(
            200,
            json={
                "freights_publications": [
                    {"id": 856796},
                    {"id": 234578},
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api_client = TransApiClient(config=config, client=client)
        response = await api_client.bulk_cancel_freight_publications(
            freight_ids=[856796, 234578],
            access_token="token",
        )
        assert isinstance(response, TransBulkCancelPublicationResponse)
        assert [item.id for item in response.freights_publications] == [856796, 234578]
