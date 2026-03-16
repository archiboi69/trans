import re

with open("trans_client/api_client.py", "r") as f:
    content = f.read()

# Remove TransRetryEvent dataclass
content = re.sub(
    r"@dataclass\(frozen=True\)\nclass TransRetryEvent:.*?(?=def _log_interaction)",
    "",
    content,
    flags=re.DOTALL | re.MULTILINE
)

# Update rate limiter to take rate as argument instead of using settings
content = re.sub(
    r"async def _acquire_trans_api_slot\(\) -> None:.*?configured_rate = max\(settings\.trans_api_rate_per_second, 1\)",
    "async def _acquire_trans_api_slot(rate_limit: int) -> None:\n    global _SHARED_RATE_LIMITER\n    global _SHARED_RATE_LIMITER_RATE\n\n    configured_rate = max(rate_limit, 1)",
    content,
    flags=re.DOTALL | re.MULTILINE
)

with open("trans_client/api_client.py", "w") as f:
    f.write(content)
