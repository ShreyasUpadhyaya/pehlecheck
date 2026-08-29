import backend.llm as llm
from backend.llm import ExplanationResult, draft_message, explain_results, parse_intake
from backend.models import Actor, RuleResult, Severity


def rule_result(rule_id: str = "R01") -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        severity=Severity.BLOCKER,
        actor=Actor.CITIZEN,
        field_read="uan_activated",
        observed_value=False,
        why=f"{rule_id}: The synthetic rule fired.",
        fix=f"{rule_id}: Apply the synthetic fix.",
        eta_days=1,
        source_note=f"{rule_id}: Synthetic source.",
    )


def test_parse_intake_degrades_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = parse_intake("My demo claim needs checking.", rule_results=[rule_result()])

    assert result.degraded is True
    assert result.rule_whys == ["R01: The synthetic rule fired."]


def test_explain_results_degrades_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = explain_results([rule_result()])

    assert result.degraded is True
    assert result.rule_whys == ["R01: The synthetic rule fired."]


def test_draft_message_degrades_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = draft_message([rule_result()], recipient=Actor.EMPLOYER)

    assert result.degraded is True
    assert result.rule_whys == ["R01: The synthetic rule fired."]


def test_explain_results_cache_is_keyed_by_rule_ids_and_language(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    llm._EXPLANATION_CACHE.clear()
    calls = []

    def fake_structured_call(schema, system_prompt, user_prompt):
        calls.append((schema, system_prompt, user_prompt))
        return ExplanationResult(language="en", sentences=["R01: Stub explanation."])

    monkeypatch.setattr(llm, "_structured_call", fake_structured_call)
    first = explain_results([rule_result()], language="en")
    second = explain_results([rule_result()], language="en")

    assert first is second
    assert len(calls) == 1
