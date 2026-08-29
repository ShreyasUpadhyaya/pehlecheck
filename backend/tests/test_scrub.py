import pytest

import backend.graph as graph
from backend.llm import IntakeResult
from backend.models import MemberProfile
from backend.scrub import scrub_text


@pytest.mark.parametrize(
    ("text", "expected_text", "expected_types"),
    [
        ("123456789012", "[REDACTED]", ["12-digit sequence"]),
        ("1234 5678 9012", "[REDACTED]", ["12-digit sequence"]),
        ("1234-5678-9012", "[REDACTED]", ["12-digit sequence"]),
        (
            "UAN 1000 1234 5678 9012",
            "UAN 1000 [REDACTED]",
            ["12-digit sequence"],
        ),
        (
            "0000-1234 5678 9012",
            "0000-[REDACTED]",
            ["12-digit sequence"],
        ),
        ("1234 5678 9012 3456", "1234 5678 9012 3456", []),
        ("12345678901234", "12345678901234", []),
        (
            "Please check my synthetic EPF claim.",
            "Please check my synthetic EPF claim.",
            [],
        ),
    ],
)
def test_scrub_text_cases(
    text: str,
    expected_text: str,
    expected_types: list[str],
) -> None:
    result = scrub_text(text)

    assert result.cleaned_text == expected_text
    assert result.stripped_types == expected_types


def test_scrub_text_still_redacts_pan_token() -> None:
    result = scrub_text("Demo ABCDE1234F is synthetic.")

    assert result.cleaned_text == "Demo [REDACTED] is synthetic."
    assert result.stripped_types == ["PAN-shaped token"]


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
