from datetime import date

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
