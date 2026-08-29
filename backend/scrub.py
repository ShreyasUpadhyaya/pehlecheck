"""Sensitive-pattern redaction before free text reaches a model."""

import re

from pydantic import BaseModel, ConfigDict, Field


class ScrubResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cleaned_text: str
    stripped_types: list[str] = Field(default_factory=list)


_SENSITIVE_TOKEN = re.compile(
    r"(?<!\d)\d{12}(?!\d)"
    r"|(?<![A-Za-z0-9])[A-Za-z]{5}\d{4}[A-Za-z](?![A-Za-z0-9])"
)
_GROUPED_DIGIT_RUN = re.compile(r"\b\d+(?:[ -]\d+)+\b")


def scrub_text(text: str) -> ScrubResult:
    """Redact 12-digit sequences and PAN-shaped tokens from free text."""

    stripped_types: list[str] = []

    def record(kind: str) -> None:
        if kind not in stripped_types:
            stripped_types.append(kind)

    def replace_grouped(match: re.Match[str]) -> str:
        raw = match.group(0)
        groups = re.split(r"[ -]", raw)
        digits_only = "".join(groups)

        if len(digits_only) == 12:
            record("12-digit sequence")
            return "[REDACTED]"

        # A leading four-digit prefix may be a separate number (for example,
        # a UAN label or a mixed-separator prefix). Redact only the trailing
        # 4-4-4 group in that case; a canonical 16/20-digit run stays intact.
        if len(groups) == 4 and all(len(group) == 4 for group in groups):
            separators = re.findall(r"[ -]", raw)
            suffix_separator = separators[1]
            has_word_prefix = bool(re.search(r"[A-Za-z]\s+$", text[: match.start()]))
            if separators[2] == suffix_separator and (
                separators[0] != suffix_separator or has_word_prefix
            ):
                record("12-digit sequence")
                return raw[: len(groups[0]) + 1] + "[REDACTED]"
        return raw

    def replace_contiguous_or_pan(match: re.Match[str]) -> str:
        digits_only = match.group(0).replace(" ", "").replace("-", "")
        kind = (
            "12-digit sequence"
            if digits_only.isdigit()
            else "PAN-shaped token"
        )
        record(kind)
        return "[REDACTED]"

    grouped_cleaned_text = _GROUPED_DIGIT_RUN.sub(replace_grouped, text)
    return ScrubResult(
        cleaned_text=_SENSITIVE_TOKEN.sub(replace_contiguous_or_pan, grouped_cleaned_text),
        stripped_types=stripped_types,
    )
