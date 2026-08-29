"""Pure rejection rules for the EPF pre-submission check."""

import re
from collections.abc import Callable
from decimal import Decimal

from .models import Actor, MemberProfile, RuleResult, Severity


SOURCE_NOTE = "EPFO public guidance; reviewed 29 Aug 2026, not authoritative."
TAX_THRESHOLD = Decimal("50000")
PURPOSE_LIMITS = {
    "MEDICAL": Decimal("100000"),
    "EDUCATION": Decimal("100000"),
    "HOUSING": Decimal("500000"),
}
CLAIM_PURPOSES = {
    "FINAL_SETTLEMENT": {"FINAL_SETTLEMENT"},
    "PENSION_WITHDRAWAL": {"PENSION_WITHDRAWAL"},
    "PARTIAL_WITHDRAWAL": set(PURPOSE_LIMITS),
}


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


def rule_r09(profile: MemberProfile) -> RuleResult | None:
    if not (
        profile.service_months < 6
        and profile.claim_type == "PENSION_WITHDRAWAL"
    ):
        return None
    return RuleResult(
        rule_id="R09",
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="service_months",
        observed_value=profile.service_months,
        why="R09: A pension withdrawal claim needs at least six months of service.",
        fix="R09: Wait until you have six months of service before submitting this claim.",
        eta_days=0,
        source_note="R09: " + SOURCE_NOTE,
    )


def rule_r10(profile: MemberProfile) -> RuleResult | None:
    if not (
        profile.service_months < 60
        and profile.claim_amount > TAX_THRESHOLD
    ):
        return None
    return RuleResult(
        rule_id="R10",
        severity=Severity.WARNING,
        actor=Actor.CITIZEN,
        field_read="service_months, claim_amount",
        observed_value={
            "service_months": profile.service_months,
            "claim_amount": profile.claim_amount,
        },
        why="R10: A claim above the tax threshold may be taxable before five years of service.",
        fix="R10: Check the tax treatment of this claim before submitting it.",
        eta_days=1,
        source_note="R10: " + SOURCE_NOTE,
    )


def rule_r11(profile: MemberProfile) -> RuleResult | None:
    if not (
        profile.employment_status == "EMPLOYED"
        and profile.claim_type == "FINAL_SETTLEMENT"
    ):
        return None
    return RuleResult(
        rule_id="R11",
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="employment_status, claim_type",
        observed_value={
            "employment_status": profile.employment_status,
            "claim_type": profile.claim_type,
        },
        why="R11: A final settlement claim cannot be filed while you are still employed.",
        fix="R11: Update your employment status after leaving employment before filing.",
        eta_days=60,
        source_note="R11: " + SOURCE_NOTE,
    )


def rule_r12(profile: MemberProfile) -> RuleResult | None:
    if len(profile.member_ids) <= 1 or not profile.untransferred_member_ids:
        return None
    return RuleResult(
        rule_id="R12",
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="member_ids",
        observed_value=profile.member_ids,
        why="R12: More than one member ID exists and at least one has not been transferred.",
        fix="R12: Transfer all previous member IDs into your current EPFO account.",
        eta_days=20,
        source_note="R12: " + SOURCE_NOTE,
    )


def rule_r13(profile: MemberProfile) -> RuleResult | None:
    if profile.eps_contribution_months >= profile.service_months:
        return None
    return RuleResult(
        rule_id="R13",
        severity=Severity.WARNING,
        actor=Actor.EMPLOYER,
        field_read="eps_contribution_months, service_months",
        observed_value={
            "eps_contribution_months": profile.eps_contribution_months,
            "service_months": profile.service_months,
        },
        why="R13: EPS contribution months are fewer than your recorded service months.",
        fix="R13: Ask your employer to reconcile the EPS contribution record.",
        eta_days=15,
        source_note="R13: " + SOURCE_NOTE,
    )


def rule_r14(profile: MemberProfile) -> RuleResult | None:
    purpose_limit = PURPOSE_LIMITS.get(profile.claim_purpose)
    if purpose_limit is None or profile.claim_amount <= purpose_limit:
        return None
    return RuleResult(
        rule_id="R14",
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="claim_amount, claim_purpose",
        observed_value={
            "claim_amount": profile.claim_amount,
            "claim_purpose": profile.claim_purpose,
        },
        why="R14: The claim amount exceeds the limit for its stated purpose.",
        fix="R14: Reduce the claim amount to the limit for this purpose.",
        eta_days=0,
        source_note="R14: " + SOURCE_NOTE,
    )


def rule_r15(profile: MemberProfile) -> RuleResult | None:
    valid_purposes = CLAIM_PURPOSES.get(profile.claim_type)
    if valid_purposes is None or profile.claim_purpose in valid_purposes:
        return None
    return RuleResult(
        rule_id="R15",
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="claim_type, claim_purpose",
        observed_value={
            "claim_type": profile.claim_type,
            "claim_purpose": profile.claim_purpose,
        },
        why="R15: The selected claim form does not match the stated purpose.",
        fix="R15: Select the claim form that matches the purpose of your claim.",
        eta_days=0,
        source_note="R15: " + SOURCE_NOTE,
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
    "R09": rule_r09,
    "R10": rule_r10,
    "R11": rule_r11,
    "R12": rule_r12,
    "R13": rule_r13,
    "R14": rule_r14,
    "R15": rule_r15,
}
