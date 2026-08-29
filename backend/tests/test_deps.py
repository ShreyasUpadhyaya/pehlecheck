from backend.deps import order_fixes
from backend.models import Actor, RuleResult, Severity


def stub(rule_id: str, severity: Severity) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        severity=severity,
        actor=Actor.CITIZEN,
        field_read="stub_field",
        observed_value="stub_value",
        why=f"{rule_id}: stub reason.",
        fix=f"{rule_id}: stub fix.",
        eta_days=0,
        source_note=f"{rule_id}: stub source.",
    )


def test_order_fixes_respects_dependencies() -> None:
    fired = [
        stub("R13", Severity.WARNING),
        stub("R05", Severity.BLOCKER),
        stub("R11", Severity.BLOCKER),
    ]

    assert [result.rule_id for result in order_fixes(fired)] == ["R11", "R05", "R13"]


def test_order_fixes_prioritizes_blockers_and_unblocks_most_rules() -> None:
    fired = [
        stub("R07", Severity.BLOCKER),
        stub("R06", Severity.BLOCKER),
        stub("R02", Severity.BLOCKER),
        stub("R08", Severity.BLOCKER),
        stub("R12", Severity.BLOCKER),
        stub("R01", Severity.BLOCKER),
        stub("R10", Severity.WARNING),
    ]

    assert [result.rule_id for result in order_fixes(fired)] == [
        "R01",
        "R08",
        "R02",
        "R06",
        "R07",
        "R12",
        "R10",
    ]


def test_order_fixes_treats_unfired_dependencies_as_satisfied() -> None:
    fired = [stub("R13", Severity.WARNING)]

    assert order_fixes(fired) == fired
