from pydantic import BaseModel, ConfigDict, Field

class TransSdkConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_base_url: str = Field(default="https://api.platform.trans.eu/ext/")
    auth_base_url: str = Field(default="https://auth.platform.trans.eu")
    api_key: str
    client_id: str
    client_secret: str
    timeout_seconds: float = Field(default=30.0)
    rate_limit_per_second: int = Field(default=5)
