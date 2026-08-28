from backend.models import MemberProfile
from backend.rules import RULES


def test_r01_fires_when_uan_is_not_activated() -> None:
    result = RULES["R01"](MemberProfile(uan_activated=False))

    assert result is not None
    assert result.rule_id == "R01"
    assert result.observed_value is False


def test_r01_does_not_fire_when_uan_is_activated() -> None:
    assert RULES["R01"](MemberProfile(uan_activated=True)) is None


def test_r03_fires_when_names_differ() -> None:
    result = RULES["R03"](
        MemberProfile(
            name_as_per_epfo="Asha Demo",
            name_as_per_aadhaar="Asha Devi Demo",
        )
    )

    assert result is not None
    assert result.rule_id == "R03"
    assert result.field_read == "name_as_per_epfo, name_as_per_aadhaar"


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
