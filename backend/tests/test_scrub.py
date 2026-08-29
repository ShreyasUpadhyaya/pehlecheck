import backend.graph as graph
from backend.llm import IntakeResult
from backend.models import MemberProfile
from backend.scrub import scrub_text


def test_scrub_text_redacts_12_digit_sequence_and_pan_token() -> None:
    result = scrub_text("Demo 123456789012 and ABCDE1234F are not real values.")

    assert result.cleaned_text == "Demo [REDACTED] and [REDACTED] are not real values."
    assert result.stripped_types == ["12-digit sequence", "PAN-shaped token"]


def test_scrub_text_reports_neither_when_no_sensitive_pattern_exists() -> None:
    result = scrub_text("Please check my synthetic EPF claim.")

    assert result.cleaned_text == "Please check my synthetic EPF claim."
    assert result.stripped_types == []


def test_intake_node_sends_only_cleaned_text_to_llm(monkeypatch) -> None:
    received: list[str] = []

    class StubLLM:
        def parse_intake(self, text: str, language: str = "en") -> IntakeResult:
            received.append(text)
            return IntakeResult(language=language)

    monkeypatch.setattr(graph, "llm", StubLLM())
    state = graph.PreflightState(
        intake_text="Synthetic 123456789012 ABCDE1234F claim.",
        profile=MemberProfile(),
    )

    updates = graph.intake(state)

    assert received == ["Synthetic [REDACTED] [REDACTED] claim."]
    assert updates["scrubbed_text"] == received[0]
    assert updates["stripped_types"] == ["12-digit sequence", "PAN-shaped token"]
