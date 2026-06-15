class AppError(Exception):
    """Base application error."""


class TransientError(AppError):
    """Retryable error — network blip, timeout, rate limit."""


class LLMTimeoutError(TransientError):
    """LLM call exceeded timeout."""


class LLMProviderError(TransientError):
    """Provider returned a transient failure."""


class ValidationError(AppError):
    """Input or output validation failed — do not retry."""


class AuthorizationError(AppError):
    """Auth failure — do not retry."""
