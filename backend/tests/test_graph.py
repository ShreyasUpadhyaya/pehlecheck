import backend.graph as graph
from backend.main import _MEMBERS
from backend.llm import ExplanationResult, IntakeResult
from backend.models import MemberProfile


class StubLLM:
    def __init__(self, clarifying_question: str | None = None) -> None:
        self.clarifying_question = clarifying_question
        self.parse_calls = 0
        self.explain_calls = 0

    def parse_intake(self, text: str, language: str = "en") -> IntakeResult:
        self.parse_calls += 1
        return IntakeResult(
            language=language,
            claim_type="FINAL_SETTLEMENT",
            claim_purpose="FINAL_SETTLEMENT",
            clarifying_question=self.clarifying_question,
        )

    def explain_results(self, results, language: str = "en") -> ExplanationResult:
        self.explain_calls += 1
        return ExplanationResult(
            language=language,
            sentences=[
                "R01: Your UAN is not activated.",
                "R99: This unmapped sentence must not be shown.",
            ],
        )


def invoke(state: graph.PreflightState) -> graph.PreflightState:
    return graph.PreflightState.model_validate(
        graph.preflight_graph.invoke(state.model_dump())
    )


def test_graph_runs_fixed_nodes_and_filters_unfired_explanations(monkeypatch) -> None:
    stub_llm = StubLLM()
    monkeypatch.setattr(graph, "llm", stub_llm)

    result = invoke(
        graph.PreflightState(
            intake_text="Check my synthetic claim.",
            profile=MemberProfile(
                uan_activated=False,
                claim_type="FINAL_SETTLEMENT",
                claim_purpose="FINAL_SETTLEMENT",
            ),
        )
    )

    assert result.node_history == [
        "intake",
        "clarify",
        "resolve_profile",
        "run_rules",
        "order_fixes",
        "explain",
        "verify",
        "render",
    ]
    assert [item.rule_id for item in result.fired_results] == ["R01", "R05"]
    assert result.rendered_sentences == ["R01: Your UAN is not activated."]
    assert result.needs_human_review == ["R99: This unmapped sentence must not be shown."]
    assert stub_llm.parse_calls == 1
    assert stub_llm.explain_calls == 1


def test_graph_clarification_loop_runs_once(monkeypatch) -> None:
    stub_llm = StubLLM(clarifying_question="Which synthetic claim type applies?")
    monkeypatch.setattr(graph, "llm", stub_llm)

    result = invoke(graph.PreflightState(profile=MemberProfile(uan_activated=False)))

    assert result.node_history.count("clarify") == 2
    assert result.clarification_loops == 1
    assert result.node_history[3:] == [
        "resolve_profile",
        "run_rules",
        "order_fixes",
        "explain",
        "verify",
        "render",
    ]


def test_loaded_profile_fields_cannot_be_overwritten_by_intake(monkeypatch) -> None:
    class RewritingStubLLM(StubLLM):
        def parse_intake(self, text: str, language: str = "en") -> IntakeResult:
            self.parse_calls += 1
            return IntakeResult(
                language=language,
                claim_type="PF withdrawal claim",
                claim_purpose="FINAL_SETTLEMENT",
            )

    monkeypatch.setattr(graph, "llm", RewritingStubLLM())
    result = invoke(
        graph.PreflightState(profile=_MEMBERS["999000000002"])
    )

    assert result.profile.claim_type == "FINAL_SETTLEMENT"
    assert {item.rule_id for item in result.fired_results} == {"R02", "R05"}
