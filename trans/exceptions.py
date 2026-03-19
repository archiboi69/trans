from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .api_client import TransNormalizedError

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
