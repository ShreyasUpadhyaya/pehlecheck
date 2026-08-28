"""Pure rejection rules for the EPF pre-submission check."""

import re
from collections.abc import Callable

from .models import Actor, MemberProfile, RuleResult, Severity


SOURCE_NOTE = "EPFO public guidance; reviewed 29 Aug 2026, not authoritative."


def _normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def rule_r01(profile: MemberProfile) -> RuleResult | None:
    if profile.uan_activated:
        return None
    return RuleResult(
        rule_id="R01",
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="uan_activated",
        observed_value=profile.uan_activated,
        why="R01: Your UAN is not activated, so this claim will be rejected.",
        fix="R01: Activate your UAN before submitting the claim.",
        eta_days=1,
        source_note="R01: " + SOURCE_NOTE,
    )


def rule_r03(profile: MemberProfile) -> RuleResult | None:
    if _normalized_name(profile.name_as_per_epfo) == _normalized_name(
        profile.name_as_per_aadhaar
    ):
        return None
    return RuleResult(
        rule_id="R03",
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="name_as_per_epfo, name_as_per_aadhaar",
        observed_value={
            "name_as_per_epfo": profile.name_as_per_epfo,
            "name_as_per_aadhaar": profile.name_as_per_aadhaar,
        },
        why="R03: The EPFO and Aadhaar names do not match after normalization.",
        fix="R03: Request a name correction so both records use the same name.",
        eta_days=15,
        source_note="R03: " + SOURCE_NOTE,
    )


Rule = Callable[[MemberProfile], RuleResult | None]
RULES: dict[str, Rule] = {
    "R01": rule_r01,
    "R03": rule_r03,
}
