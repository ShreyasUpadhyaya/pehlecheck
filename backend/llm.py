"""Structured, optional LLM helpers for intake, explanations, and drafts."""

import os
from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from .models import Actor, RuleResult


_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
_T = TypeVar("_T", bound=BaseModel)


class IntakeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degraded: bool = False
    language: str
    claim_type: str | None = None
    claim_purpose: str | None = None
    clarifying_question: str | None = None
    rule_whys: list[str] = Field(default_factory=list)


class ExplanationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degraded: bool = False
    language: str
    sentences: list[str] = Field(default_factory=list)
    rule_whys: list[str] = Field(default_factory=list)


class DraftMessageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degraded: bool = False
    language: str
    recipient: Actor
    message: str = ""
    rule_whys: list[str] = Field(default_factory=list)


_EXPLANATION_CACHE: dict[tuple[tuple[str, ...], str], ExplanationResult] = {}


def _rule_whys(results: list[RuleResult]) -> list[str]:
    return [result.why for result in results]


def _structured_call(
    schema: type[_T],
    system_prompt: str,
    user_prompt: str,
) -> _T:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    response = client.responses.parse(
        model=_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        text_format=schema,
    )
    parsed: Any = getattr(response, "output_parsed", None)
    if parsed is None:
        raise ValueError("structured response did not contain a parsed object")
    return schema.model_validate(parsed)


def parse_intake(
    text: str,
    language: str = "en",
    rule_results: list[RuleResult] | None = None,
) -> IntakeResult:
    """Parse citizen intake into a validated structured object."""

    raw_whys = _rule_whys(rule_results or [])
    try:
        result = _structured_call(
            IntakeResult,
            "Extract claim type and purpose from the citizen's text. Return only the schema.",
            f"Language: {language}\nCitizen text: {text}",
        )
        return result.model_copy(update={"degraded": False, "rule_whys": []})
    except Exception:
        return IntakeResult(degraded=True, language=language, rule_whys=raw_whys)


def explain_results(
    results: list[RuleResult],
    language: str = "en",
) -> ExplanationResult:
    """Explain fired rules with a validated structured response and cache hits."""

    cache_key = (tuple(result.rule_id for result in results), language)
    cached = _EXPLANATION_CACHE.get(cache_key)
    if cached is not None:
        return cached

    raw_whys = _rule_whys(results)
    try:
        result = _structured_call(
            ExplanationResult,
            "Explain each supplied rule. Every sentence must include its rule_id. Return only the schema.",
            f"Language: {language}\nRule results: {results}",
        )
        result = result.model_copy(update={"degraded": False, "rule_whys": []})
        _EXPLANATION_CACHE[cache_key] = result
        return result
    except Exception:
        return ExplanationResult(
            degraded=True,
            language=language,
            rule_whys=raw_whys,
        )


def draft_message(
    results: list[RuleResult],
    recipient: Actor = Actor.EMPLOYER,
    language: str = "en",
) -> DraftMessageResult:
    """Draft a validated message for the responsible actor."""

    raw_whys = _rule_whys(results)
    try:
        result = _structured_call(
            DraftMessageResult,
            "Draft a concise message about the supplied rule results. Every sentence must include its rule_id. Return only the schema.",
            f"Language: {language}\nRecipient: {recipient.value}\nRule results: {results}",
        )
        return result.model_copy(
            update={"degraded": False, "language": language, "recipient": recipient, "rule_whys": []}
        )
    except Exception:
        return DraftMessageResult(
            degraded=True,
            language=language,
            recipient=recipient,
            rule_whys=raw_whys,
        )
