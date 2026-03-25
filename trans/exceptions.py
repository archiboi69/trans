from typing import Any, TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from .api_client import TransNormalizedError

def format_network_error(exc: Exception) -> tuple[str, dict[str, Any]]:
    """Format an exception into a human-readable message and a structured dictionary."""
    exc_type = type(exc).__name__
    exc_str = str(exc).strip()
    exc_repr = repr(exc)
    
    error_message = exc_str if exc_str else exc_type
    
    error_category = "transport_error"
    if isinstance(exc, httpx.TimeoutException):
        error_category = "timeout"
    elif isinstance(exc, httpx.ConnectError):
        error_category = "connection_error"
        
    error_dict = {
        "type": exc_type,
        "category": error_category,
        "retryable": True,
        "detail": error_message,
        "repr": exc_repr,
    }
    
    return error_message, error_dict

class TransSdkError(Exception):
    """Base class for all Trans SDK errors."""
    pass

class TransAuthError(TransSdkError):
    """Base class for Trans authentication errors."""
    pass

class TransAuthRejectedError(TransAuthError):
    """Raised when Trans rejects the authentication credentials or grant."""
    pass

class TransApiError(TransSdkError):
    """Raised when the Trans API returns an error response."""
    def __init__(self, normalized: "TransNormalizedError"):
        self.normalized = normalized
        super().__init__(str(normalized))

class TransApiUnreachableError(TransSdkError):
    """Raised when the Trans API is network-unreachable."""
    pass

class TransInvalidResponseError(TransSdkError):
    """Raised when the Trans API returns a response that cannot be parsed."""
    pass
