from backend.models import MemberProfile
from backend.voi import questions_worth_asking


def test_questions_worth_asking_returns_rule_changing_question() -> None:
    questions = questions_worth_asking(
        MemberProfile(uan_activated=True),
        ["uan_activated"],
    )

    assert len(questions) == 1
    question = questions[0]
    assert question.field == "uan_activated"
    assert question.rule_ids == ["R01"]
    assert question.flip_count == 1
    assert set(question.options) == {False, True}
    assert "R01" in question.prompt


def test_questions_worth_asking_caps_at_one_and_ranks_by_flips() -> None:
    questions = questions_worth_asking(
        MemberProfile(
            claim_type="FINAL_SETTLEMENT",
            employment_status="EMPLOYED",
            date_of_exit=None,
        ),
        ["employment_status", "claim_type"],
    )

    assert len(questions) == 1
    assert questions[0].field == "claim_type"
    assert questions[0].flip_count > 1


def test_questions_worth_asking_omits_fields_that_change_no_rule() -> None:
    questions = questions_worth_asking(
        MemberProfile(claim_type=""),
        ["claim_purpose", "not_a_member_field"],
    )

    assert questions == []
