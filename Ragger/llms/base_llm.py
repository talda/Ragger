from abc import ABC, abstractmethod
import httpx


class LanguageModel(ABC):
    def __init__(self):
        self.client = None  # Initialized in subclasses

    @abstractmethod
    def create_response(
        self, messages: list[str], system_prompt: str, max_tokens: int = 4096
    ):
        pass


def is_rate_limit_error(exception):
    """Return True if the exception is a rate limit error (HTTP 429)."""
    return (
        isinstance(exception, httpx.HTTPStatusError)
        and exception.response.status_code == 429
    )
