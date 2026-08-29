"""Sensitive-pattern redaction before free text reaches a model."""

import re

from pydantic import BaseModel, ConfigDict, Field


class ScrubResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cleaned_text: str
    stripped_types: list[str] = Field(default_factory=list)


_SENSITIVE_TOKEN = re.compile(
    r"(?<!\d)(?:\d{12}|\d{4}(?P<aadhaar_separator>[ -])\d{4}(?P=aadhaar_separator)\d{4})(?!\d)"
    r"|(?<![A-Za-z0-9])[A-Za-z]{5}\d{4}[A-Za-z](?![A-Za-z0-9])"
)


def scrub_text(text: str) -> ScrubResult:
    """Redact 12-digit sequences and PAN-shaped tokens from free text."""

    stripped_types: list[str] = []

    def replace(match: re.Match[str]) -> str:
        digits_only = match.group(0).replace(" ", "").replace("-", "")
        kind = (
            "12-digit sequence"
            if digits_only.isdigit()
            else "PAN-shaped token"
        )
        if kind not in stripped_types:
            stripped_types.append(kind)
        return "[REDACTED]"

    return ScrubResult(
        cleaned_text=_SENSITIVE_TOKEN.sub(replace, text),
        stripped_types=stripped_types,
    )
