"""The fixed preflight workflow, with one bounded clarification loop."""

import re

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from . import llm
from .deps import order_fixes as order_rule_fixes
from .llm import ExplanationResult, IntakeResult
from .models import MemberProfile, RuleResult
from .rules import RULES
from .scrub import scrub_text


_RULE_ID_PATTERN = re.compile(r"\bR\d{2}\b")


class PreflightState(BaseModel):
    """Typed state passed through every preflight workflow node."""

    model_config = ConfigDict(extra="forbid")

    intake_text: str = ""
    scrubbed_text: str = ""
    stripped_types: list[str] = Field(default_factory=list)
    language: str = "en"
    profile: MemberProfile = Field(default_factory=MemberProfile)
    unknown_fields: list[str] = Field(default_factory=list)
    intake_result: IntakeResult | None = None
    clarification_question: str | None = None
    clarification_answer: str | None = None
    clarification_loops: int = Field(default=0, ge=0, le=1)
    clarification_loop_pending: bool = False
    fired_results: list[RuleResult] = Field(default_factory=list)
    ordered_results: list[RuleResult] = Field(default_factory=list)
    explanation: ExplanationResult | None = None
    verified_sentences: list[str] = Field(default_factory=list)
    needs_human_review: list[str] = Field(default_factory=list)
    rendered_sentences: list[str] = Field(default_factory=list)
    node_history: list[str] = Field(default_factory=list)


def _history(state: PreflightState, node_name: str) -> list[str]:
    return [*state.node_history, node_name]


def intake(state: PreflightState) -> dict[str, object]:
    """Parse free-text intake through the LLM boundary."""

    scrubbed = scrub_text(state.intake_text)
    result = llm.parse_intake(scrubbed.cleaned_text, language=state.language)
    return {
        "scrubbed_text": scrubbed.cleaned_text,
        "stripped_types": scrubbed.stripped_types,
        "intake_result": result,
        "clarification_question": result.clarifying_question,
        "node_history": _history(state, "intake"),
    }


def clarify(state: PreflightState) -> dict[str, object]:
    """Record at most one clarification loop before continuing the workflow."""

    should_loop = (
        state.clarification_question is not None and state.clarification_loops == 0
    )
    return {
        "clarification_loops": state.clarification_loops + int(should_loop),
        "clarification_loop_pending": should_loop,
        "node_history": _history(state, "clarify"),
    }


def _after_clarify(state: PreflightState) -> str:
    return "clarify" if state.clarification_loop_pending else "resolve_profile"


def resolve_profile(state: PreflightState) -> dict[str, object]:
    """Fill explicitly unknown, empty fields without replacing profile truth."""

    profile_updates: dict[str, str] = {}
    if state.intake_result is not None:
        if (
            "claim_type" in state.unknown_fields
            and not state.profile.claim_type
            and state.intake_result.claim_type is not None
        ):
            profile_updates["claim_type"] = state.intake_result.claim_type
        if (
            "claim_purpose" in state.unknown_fields
            and not state.profile.claim_purpose
            and state.intake_result.claim_purpose is not None
        ):
            profile_updates["claim_purpose"] = state.intake_result.claim_purpose
    profile = state.profile.model_copy(update=profile_updates)
    return {"profile": profile, "node_history": _history(state, "resolve_profile")}


def run_rules(state: PreflightState) -> dict[str, object]:
    """Run the deterministic rules engine without I/O or model access."""

    fired_results = [
        result for rule in RULES.values() if (result := rule(state.profile)) is not None
    ]
    return {
        "fired_results": fired_results,
        "node_history": _history(state, "run_rules"),
    }


def order_fixes(state: PreflightState) -> dict[str, object]:
    """Order deterministic rule results without I/O or model access."""

    return {
        "ordered_results": order_rule_fixes(state.fired_results),
        "node_history": _history(state, "order_fixes"),
    }


def explain(state: PreflightState) -> dict[str, object]:
    """Explain ordered results through the LLM boundary."""

    result = llm.explain_results(state.ordered_results, language=state.language)
    return {"explanation": result, "node_history": _history(state, "explain")}


def verify(state: PreflightState) -> dict[str, object]:
    """Keep only explanation sentences whose rule IDs belong to fired rules."""

    fired_ids = {result.rule_id for result in state.fired_results}
    explanation = state.explanation or ExplanationResult(language=state.language)
    sentences = explanation.sentences or explanation.rule_whys
    verified_sentences: list[str] = []
    needs_human_review = list(state.needs_human_review)

    for sentence in sentences:
        sentence_rule_ids = set(_RULE_ID_PATTERN.findall(sentence))
        if sentence_rule_ids and sentence_rule_ids <= fired_ids:
            verified_sentences.append(sentence)
        else:
            needs_human_review.append(sentence)

    return {
        "verified_sentences": verified_sentences,
        "needs_human_review": needs_human_review,
        "node_history": _history(state, "verify"),
    }


def render(state: PreflightState) -> dict[str, object]:
    """Expose only verified, rule-mapped sentences to the presentation layer."""

    return {
        "rendered_sentences": state.verified_sentences,
        "node_history": _history(state, "render"),
    }


def build_graph():
    workflow = StateGraph(PreflightState)
    workflow.add_node("intake", intake)
    workflow.add_node("clarify", clarify)
    workflow.add_node("resolve_profile", resolve_profile)
    workflow.add_node("run_rules", run_rules)
    workflow.add_node("order_fixes", order_fixes)
    workflow.add_node("explain", explain)
    workflow.add_node("verify", verify)
    workflow.add_node("render", render)

    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "clarify")
    workflow.add_conditional_edges(
        "clarify",
        _after_clarify,
        {"clarify": "clarify", "resolve_profile": "resolve_profile"},
    )
    workflow.add_edge("resolve_profile", "run_rules")
    workflow.add_edge("run_rules", "order_fixes")
    workflow.add_edge("order_fixes", "explain")
    workflow.add_edge("explain", "verify")
    workflow.add_edge("verify", "render")
    workflow.add_edge("render", END)
    return workflow.compile()


preflight_graph = build_graph()
