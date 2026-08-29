"""Value-of-information gate for one useful clarification question."""

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import MemberProfile
from .rules import RULES, PURPOSE_LIMITS, TAX_THRESHOLD


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    prompt: str
    options: list[Any]
    rule_ids: list[str] = Field(default_factory=list)
    flip_count: int = Field(ge=1)


_CLAIM_TYPES = (
    "FINAL_SETTLEMENT",
    "PENSION_WITHDRAWAL",
    "PARTIAL_WITHDRAWAL",
)
_CLAIM_PURPOSES = (
    "FINAL_SETTLEMENT",
    "PENSION_WITHDRAWAL",
    *PURPOSE_LIMITS,
)


def _unique(values: list[Any]) -> list[Any]:
    unique: list[Any] = []
    for value in values:
        if not any(value == existing for existing in unique):
            unique.append(value)
    return unique


def _plausible_values(profile: MemberProfile, field: str) -> list[Any]:
    current = getattr(profile, field)
    if field in {
        "uan_activated",
        "kyc_approved",
        "bank_ifsc_verified",
        "account_is_joint",
        "aadhaar_seeded",
    }:
        return [current, False, True]
    if field in {"dob_epfo", "dob_aadhaar", "date_of_exit"}:
        return _unique([current, None, date(1990, 1, 1)])
    if field == "service_months":
        return _unique([current, 0, 5, 6, 59, 60])
    if field == "eps_contribution_months":
        return _unique([current, 0, 5, 12, 60])
    if field == "claim_amount":
        return _unique(
            [current, Decimal("0"), TAX_THRESHOLD, TAX_THRESHOLD + 1, Decimal("100001")]
        )
    if field == "claim_type":
        return _unique([current, *_CLAIM_TYPES, "OTHER"])
    if field == "claim_purpose":
        return _unique([current, *_CLAIM_PURPOSES, "OTHER"])
    if field == "employment_status":
        return _unique([current, "EMPLOYED", "NOT_EMPLOYED"])
    if field in {"member_ids", "untransferred_member_ids"}:
        return _unique(
            [
                current,
                [],
                ["MEMBER-DEMO-1"],
                ["MEMBER-DEMO-1", "MEMBER-DEMO-2"],
            ]
        )
    if field in {"name_as_per_epfo", "name_as_per_aadhaar", "account_holder_name"}:
        return _unique([current, "Asha Demo", "Bina Demo"])
    return []


def _fired_ids(profile: MemberProfile) -> set[str]:
    return {
        rule_id
        for rule_id, rule in RULES.items()
        if rule(profile) is not None
    }


def _question_for_field(profile: MemberProfile, field: str) -> Question | None:
    options = _plausible_values(profile, field)
    if len(options) < 2:
        return None

    statuses = [
        _fired_ids(profile.model_copy(update={field: value}))
        for value in options
    ]
    all_rule_ids = set().union(*statuses)
    flipped_rule_ids = sorted(
        rule_id
        for rule_id in all_rule_ids
        if len({rule_id in fired for fired in statuses}) > 1
    )
    if not flipped_rule_ids:
        return None

    readable_field = field.replace("_", " ")
    rule_prefix = ", ".join(flipped_rule_ids)
    return Question(
        field=field,
        prompt=f"{rule_prefix}: What is the {readable_field}?",
        options=options,
        rule_ids=flipped_rule_ids,
        flip_count=len(flipped_rule_ids),
    )


def questions_worth_asking(
    profile: MemberProfile,
    unknown_fields: list[str],
) -> list[Question]:
    """Return at most the highest-value rule-changing clarification question."""

    candidates = [
        _question_for_field(profile, field)
        for field in unknown_fields
        if field in MemberProfile.model_fields
    ]
    questions = [question for question in candidates if question is not None]
    questions.sort(key=lambda question: (-question.flip_count, question.field))
    return questions[:1]
