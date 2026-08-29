"""Dependency-aware ordering for fired rule fixes."""

from .models import RuleResult, Severity


# Each key depends on the rule IDs in its value.  An edge is therefore added
# from every dependency to the rule that depends on it.
DEPENDENCIES: dict[str, frozenset[str]] = {
    "R02": frozenset({"R08"}),
    "R06": frozenset({"R02"}),
    "R07": frozenset({"R02"}),
    "R05": frozenset({"R11"}),
    "R12": frozenset({"R01"}),
    "R13": frozenset({"R05"}),
}


_SEVERITY_RANK = {
    Severity.BLOCKER: 0,
    Severity.WARNING: 1,
    Severity.INFO: 2,
}


def _priority(
    result: RuleResult,
    dependents: dict[str, set[str]],
) -> tuple[int, int, str]:
    """Return the stable priority key for a currently-ready result."""

    return (
        _SEVERITY_RANK[result.severity],
        -len(dependents[result.rule_id]),
        result.rule_id,
    )


def order_fixes(fired: list[RuleResult]) -> list[RuleResult]:
    """Topologically order fired fixes, prioritizing blockers and leverage.

    Dependencies that are not themselves fired are considered already
    satisfied: this function orders only the supplied results.
    """

    by_id = {result.rule_id: result for result in fired}
    if len(by_id) != len(fired):
        raise ValueError("fired rule IDs must be unique")

    fired_ids = set(by_id)
    remaining_dependencies = {
        rule_id: set(DEPENDENCIES.get(rule_id, frozenset()) & fired_ids)
        for rule_id in fired_ids
    }
    dependents = {rule_id: set() for rule_id in fired_ids}
    for rule_id, dependencies in remaining_dependencies.items():
        for dependency in dependencies:
            dependents[dependency].add(rule_id)

    ordered: list[RuleResult] = []
    ready: set[str] = {
        rule_id
        for rule_id, dependencies in remaining_dependencies.items()
        if not dependencies
    }

    while ready:
        next_id = min(
            ready,
            key=lambda rule_id: _priority(by_id[rule_id], dependents),
        )
        ready.remove(next_id)
        ordered.append(by_id[next_id])

        for dependent in dependents[next_id]:
            remaining_dependencies[dependent].remove(next_id)
            if not remaining_dependencies[dependent]:
                ready.add(dependent)

    if len(ordered) != len(fired):
        raise ValueError("rule dependency graph contains a cycle")
    return ordered
