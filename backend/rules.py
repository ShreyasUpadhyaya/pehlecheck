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


def rule_r02(profile: MemberProfile) -> RuleResult | None:
    if profile.kyc_approved:
        return None
    return RuleResult(
        rule_id="R02",
        severity=Severity.BLOCKER,
        actor=Actor.EMPLOYER,
        field_read="kyc_approved",
        observed_value=profile.kyc_approved,
        why="R02: Your KYC is not approved, so this claim will be rejected.",
        fix="R02: Ask your employer to approve your KYC details.",
        eta_days=7,
        source_note="R02: " + SOURCE_NOTE,
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


def rule_r04(profile: MemberProfile) -> RuleResult | None:
    if profile.dob_epfo == profile.dob_aadhaar:
        return None
    return RuleResult(
        rule_id="R04",
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="dob_epfo, dob_aadhaar",
        observed_value={
            "dob_epfo": profile.dob_epfo,
            "dob_aadhaar": profile.dob_aadhaar,
        },
        why="R04: Your dates of birth do not match between EPFO and Aadhaar.",
        fix="R04: Request a date-of-birth correction so both records match.",
        eta_days=15,
        source_note="R04: " + SOURCE_NOTE,
    )


def rule_r05(profile: MemberProfile) -> RuleResult | None:
    if profile.date_of_exit is not None or profile.claim_type != "FINAL_SETTLEMENT":
        return None
    return RuleResult(
        rule_id="R05",
        severity=Severity.BLOCKER,
        actor=Actor.EMPLOYER,
        field_read="date_of_exit",
        observed_value=profile.date_of_exit,
        why="R05: Your date of exit is missing for a final settlement claim.",
        fix="R05: Ask your employer to record your date of exit.",
        eta_days=10,
        source_note="R05: " + SOURCE_NOTE,
    )


def rule_r06(profile: MemberProfile) -> RuleResult | None:
    if profile.bank_ifsc_verified:
        return None
    return RuleResult(
        rule_id="R06",
        severity=Severity.BLOCKER,
        actor=Actor.BANK,
        field_read="bank_ifsc_verified",
        observed_value=profile.bank_ifsc_verified,
        why="R06: Your bank IFSC has not been verified, so this claim may be rejected.",
        fix="R06: Ask your bank to verify or update the IFSC linked to your account.",
        eta_days=3,
        source_note="R06: " + SOURCE_NOTE,
    )


def rule_r07(profile: MemberProfile) -> RuleResult | None:
    names_differ = _normalized_name(profile.account_holder_name) != _normalized_name(
        profile.name_as_per_epfo
    )
    if not names_differ and not profile.account_is_joint:
        return None
    return RuleResult(
        rule_id="R07",
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="account_holder_name, name_as_per_epfo",
        observed_value={
            "account_holder_name": profile.account_holder_name,
            "name_as_per_epfo": profile.name_as_per_epfo,
            "account_is_joint": profile.account_is_joint,
        },
        why="R07: The bank account holder does not match your EPFO name or the account is joint.",
        fix="R07: Use a single-holder bank account whose name matches your EPFO record.",
        eta_days=5,
        source_note="R07: " + SOURCE_NOTE,
    )


def rule_r08(profile: MemberProfile) -> RuleResult | None:
    if profile.aadhaar_seeded:
        return None
    return RuleResult(
        rule_id="R08",
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="aadhaar_seeded",
        observed_value=profile.aadhaar_seeded,
        why="R08: Your Aadhaar is not seeded with your EPFO record.",
        fix="R08: Seed your Aadhaar with your EPFO record before submitting the claim.",
        eta_days=3,
        source_note="R08: " + SOURCE_NOTE,
    )


Rule = Callable[[MemberProfile], RuleResult | None]
RULES: dict[str, Rule] = {
    "R01": rule_r01,
    "R02": rule_r02,
    "R03": rule_r03,
    "R04": rule_r04,
    "R05": rule_r05,
    "R06": rule_r06,
    "R07": rule_r07,
    "R08": rule_r08,
}
