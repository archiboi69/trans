# trans SDK

A standalone Python SDK for the Trans.eu API.

## Installation

```bash
uv add "git+ssh://git@github.com/archiboi69/trans.git"
```

## Usage

### Configuration

```python
from trans import TransSdkConfig, TransAuthClient, TransApiClient

config = TransSdkConfig(
    api_key="your_api_key",
    client_id="your_client_id",
    client_secret="your_client_secret",
)
```

### Authentication

```python
auth_client = TransAuthClient(config=config)

# Build OAuth URL
auth_url = auth_client.build_auth_url(redirect_uri="https://your-app.com/callback")

# Exchange code for token
token_response = await auth_client.exchange_code_for_token(code="...", redirect_uri="...")

# Set refresh token manually if you have one
auth_client.set_refresh_token("your_refresh_token")

# Get access token (refreshes automatically if expired)
access_token = await auth_client.get_access_token()
```

### API Requests

```python
api_client = TransApiClient(config=config)

# New freight
from trans import TransFreightExchangeRequest
payload = TransFreightExchangeRequest(...)
response = await api_client.new_freight_to_freight_exchange(
    payload=payload,
    access_token=access_token
)

# Refresh freight publication
await api_client.refresh_freight_publication(
    freight_id=123,
    access_token=access_token
)

# Cancel freight publication
await api_client.cancel_freight_publication(
    freight_id=123,
    access_token=access_token
)
```

### Error Handling

```python
from trans import TransApiError, TransApiUnreachableError

try:
    await api_client.refresh_freight_publication(...)
except TransApiError as e:
    print(f"API Error: {e.normalized.detail}")
    if e.normalized.status_code == 429:
        print(f"Retry after: {e.normalized.retry_after_seconds}s")
except TransApiUnreachableError:
    print("Network issue")
```

## Development and Proof

### Running Tests
```bash
uv run pytest
```

### Smoke Test (Imports and Configuration)
```bash
uv run python -c "from trans import TransApiClient, TransAuthClient, TransSdkConfig; print("SDK Ready")"
```
