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
