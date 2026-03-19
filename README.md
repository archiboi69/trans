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

# Get auth headers for manual requests
headers = await auth_client.auth_headers()
```

### API Requests

```python
api_client = TransApiClient(config=config)

# New freight
response = await api_client.new_freight_to_freight_exchange(
    payload=...,
    access_token=token_response.access_token
)
```

### Error Handling

```python
from trans import TransApiError, TransApiUnreachableError

try:
    await api_client.refresh_freight_publication(...)
except TransApiError as e:
    print(f"API Error: {e.normalized.detail}")
except TransApiUnreachableError:
    print("Network issue")
```
