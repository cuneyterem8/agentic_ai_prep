import re


_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_PATTERN = re.compile(r"\b\+?\d[\d\s\-()]{8,}\d\b")
_IBAN_PATTERN = re.compile(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", re.IGNORECASE)


def mask_pii(text: str) -> str:
    """Mask common PII patterns before writing audit/tool logs."""
    masked = _EMAIL_PATTERN.sub("[EMAIL_REDACTED]", text)
    masked = _PHONE_PATTERN.sub("[PHONE_REDACTED]", masked)
    masked = _IBAN_PATTERN.sub("[IBAN_REDACTED]", masked)
    return masked


def mask_mapping(values: dict) -> dict:
    masked: dict = {}
    for key, value in values.items():
        if isinstance(value, dict):
            masked[key] = mask_mapping(value)
        else:
            masked[key] = mask_pii(str(value))
    return masked
