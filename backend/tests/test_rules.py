from datetime import date
from decimal import Decimal

from backend.models import MemberProfile, Severity
from backend.rules import RULES


def test_r01_fires_when_uan_is_not_activated() -> None:
    profile = MemberProfile(uan_activated=False)
    result = RULES["R01"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R01"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "uan_activated"
    assert result.observed_value == profile.uan_activated


def test_r01_does_not_fire_when_uan_is_activated() -> None:
    assert RULES["R01"](MemberProfile(uan_activated=True)) is None


def test_r02_fires_when_kyc_is_not_approved() -> None:
    profile = MemberProfile(kyc_approved=False)
    result = RULES["R02"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R02"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "kyc_approved"
    assert result.observed_value == profile.kyc_approved


def test_r02_does_not_fire_when_kyc_is_approved() -> None:
    assert RULES["R02"](MemberProfile(kyc_approved=True)) is None


def test_r03_fires_when_names_differ() -> None:
    profile = MemberProfile(
        name_as_per_epfo="Asha Demo",
        name_as_per_aadhaar="Asha Devi Demo",
    )
    result = RULES["R03"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R03"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "name_as_per_epfo, name_as_per_aadhaar"
    assert result.observed_value == {
        "name_as_per_epfo": profile.name_as_per_epfo,
        "name_as_per_aadhaar": profile.name_as_per_aadhaar,
    }


def test_r03_does_not_fire_for_equivalent_normalized_names() -> None:
    assert (
        RULES["R03"](
            MemberProfile(
                name_as_per_epfo="Asha-Demo",
                name_as_per_aadhaar=" asha demo ",
            )
        )
        is None
    )


def test_r04_fires_when_dates_of_birth_differ() -> None:
    profile = MemberProfile(
        dob_epfo=date(1990, 1, 2),
        dob_aadhaar=date(1990, 1, 3),
    )
    result = RULES["R04"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R04"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "dob_epfo, dob_aadhaar"
    assert result.observed_value == {
        "dob_epfo": profile.dob_epfo,
        "dob_aadhaar": profile.dob_aadhaar,
    }


def test_r04_does_not_fire_when_dates_of_birth_match() -> None:
    dob = date(1990, 1, 2)
    assert RULES["R04"](MemberProfile(dob_epfo=dob, dob_aadhaar=dob)) is None


def test_r05_fires_when_final_settlement_has_no_exit_date() -> None:
    profile = MemberProfile(claim_type="FINAL_SETTLEMENT", date_of_exit=None)
    result = RULES["R05"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R05"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "date_of_exit"
    assert result.observed_value == profile.date_of_exit


def test_r05_does_not_fire_when_final_settlement_has_an_exit_date() -> None:
    assert (
        RULES["R05"](
            MemberProfile(
                claim_type="FINAL_SETTLEMENT",
                date_of_exit=date(2026, 1, 2),
            )
        )
        is None
    )


def test_r06_fires_when_ifsc_is_not_verified() -> None:
    profile = MemberProfile(bank_ifsc_verified=False)
    result = RULES["R06"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R06"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "bank_ifsc_verified"
    assert result.observed_value == profile.bank_ifsc_verified


def test_r06_does_not_fire_when_ifsc_is_verified() -> None:
    assert RULES["R06"](MemberProfile(bank_ifsc_verified=True)) is None


def test_r07_fires_when_account_holder_name_differs() -> None:
    profile = MemberProfile(
        account_holder_name="Bina Demo",
        name_as_per_epfo="Asha Demo",
    )
    result = RULES["R07"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R07"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "account_holder_name, name_as_per_epfo"
    assert result.observed_value == {
        "account_holder_name": profile.account_holder_name,
        "name_as_per_epfo": profile.name_as_per_epfo,
        "account_is_joint": profile.account_is_joint,
    }


def test_r07_does_not_fire_for_matching_single_holder_account() -> None:
    assert (
        RULES["R07"](
            MemberProfile(
                account_holder_name="Asha-Demo",
                name_as_per_epfo=" asha demo ",
                account_is_joint=False,
            )
        )
        is None
    )


def test_r08_fires_when_aadhaar_is_not_seeded() -> None:
    profile = MemberProfile(aadhaar_seeded=False)
    result = RULES["R08"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R08"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "aadhaar_seeded"
    assert result.observed_value == profile.aadhaar_seeded


def test_r08_does_not_fire_when_aadhaar_is_seeded() -> None:
    assert RULES["R08"](MemberProfile(aadhaar_seeded=True)) is None


def test_r09_fires_for_short_pension_withdrawal_service() -> None:
    profile = MemberProfile(service_months=5, claim_type="PENSION_WITHDRAWAL")
    result = RULES["R09"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R09"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "service_months"
    assert result.observed_value == profile.service_months


def test_r09_does_not_fire_for_sufficient_pension_withdrawal_service() -> None:
    assert (
        RULES["R09"](
            MemberProfile(service_months=6, claim_type="PENSION_WITHDRAWAL")
        )
        is None
    )


def test_r10_fires_for_large_claim_before_five_years() -> None:
    profile = MemberProfile(service_months=59, claim_amount=Decimal("50001"))
    result = RULES["R10"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R10"
    assert result.severity == Severity.WARNING
    assert result.field_read == "service_months, claim_amount"
    assert result.observed_value == {
        "service_months": profile.service_months,
        "claim_amount": profile.claim_amount,
    }


def test_r10_does_not_fire_for_small_claim_before_five_years() -> None:
    assert (
        RULES["R10"](
            MemberProfile(service_months=59, claim_amount=Decimal("50000"))
        )
        is None
    )


def test_r11_fires_for_final_settlement_while_employed() -> None:
    profile = MemberProfile(
        employment_status="EMPLOYED",
        claim_type="FINAL_SETTLEMENT",
    )
    result = RULES["R11"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R11"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "employment_status, claim_type"
    assert result.observed_value == {
        "employment_status": profile.employment_status,
        "claim_type": profile.claim_type,
    }


def test_r11_does_not_fire_for_final_settlement_after_employment() -> None:
    assert (
        RULES["R11"](
            MemberProfile(
                employment_status="NOT_EMPLOYED",
                claim_type="FINAL_SETTLEMENT",
            )
        )
        is None
    )


def test_r12_fires_when_a_member_id_is_untransferred() -> None:
    profile = MemberProfile(
        member_ids=["MEMBER-DEMO-1", "MEMBER-DEMO-2"],
        untransferred_member_ids=["MEMBER-DEMO-1"],
    )
    result = RULES["R12"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R12"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "member_ids"
    assert result.observed_value == profile.member_ids


def test_r12_does_not_fire_when_all_member_ids_are_transferred() -> None:
    assert (
        RULES["R12"](
            MemberProfile(
                member_ids=["MEMBER-DEMO-1", "MEMBER-DEMO-2"],
                untransferred_member_ids=[],
            )
        )
        is None
    )


def test_r13_fires_when_eps_months_are_short_of_service_months() -> None:
    profile = MemberProfile(eps_contribution_months=11, service_months=12)
    result = RULES["R13"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R13"
    assert result.severity == Severity.WARNING
    assert result.field_read == "eps_contribution_months, service_months"
    assert result.observed_value == {
        "eps_contribution_months": profile.eps_contribution_months,
        "service_months": profile.service_months,
    }


def test_r13_does_not_fire_when_eps_months_cover_service_months() -> None:
    assert (
        RULES["R13"](
            MemberProfile(eps_contribution_months=12, service_months=12)
        )
        is None
    )


def test_r14_fires_when_amount_exceeds_purpose_limit() -> None:
    profile = MemberProfile(
        claim_amount=Decimal("100001"),
        claim_purpose="MEDICAL",
    )
    result = RULES["R14"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R14"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "claim_amount, claim_purpose"
    assert result.observed_value == {
        "claim_amount": profile.claim_amount,
        "claim_purpose": profile.claim_purpose,
    }


def test_r14_does_not_fire_when_amount_is_at_purpose_limit() -> None:
    assert (
        RULES["R14"](
            MemberProfile(
                claim_amount=Decimal("100000"),
                claim_purpose="MEDICAL",
            )
        )
        is None
    )


def test_r15_fires_when_claim_form_does_not_match_purpose() -> None:
    profile = MemberProfile(
        claim_type="FINAL_SETTLEMENT",
        claim_purpose="MEDICAL",
    )
    result = RULES["R15"](profile)

    # Copy this assertion block when adding a rule.
    assert result is not None
    assert result.rule_id == "R15"
    assert result.severity == Severity.BLOCKER
    assert result.field_read == "claim_type, claim_purpose"
    assert result.observed_value == {
        "claim_type": profile.claim_type,
        "claim_purpose": profile.claim_purpose,
    }


def test_r15_does_not_fire_when_claim_form_matches_purpose() -> None:
    assert (
        RULES["R15"](
            MemberProfile(
                claim_type="FINAL_SETTLEMENT",
                claim_purpose="FINAL_SETTLEMENT",
            )
        )
        is None
    )
