from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_preflight_uses_synthetic_profile() -> None:
    response = client.post(
        "/preflight",
        json={"uan": "999000000002", "intake_text": "Check my claim."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["name_as_per_epfo"] == "Bina Demo"
    assert {result["rule_id"] for result in body["ordered_issues"]} == {"R02", "R05"}


def test_override_recomputes_profile() -> None:
    preflight_response = client.post(
        "/preflight",
        json={"uan": "999000000002"},
    )
    state = preflight_response.json()

    response = client.post(
        "/override",
        json={
            "state": state,
            "overrides": {"kyc_approved": True, "date_of_exit": "2025-06-01"},
        },
    )

    assert response.status_code == 200
    assert response.json()["ordered_issues"] == []


def test_submit_mock_requires_review_and_no_blockers() -> None:
    response = client.post(
        "/submit-mock",
        json={
            "state": client.post("/preflight", json={"uan": "999000000001"}).json(),
            "review_confirmed": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "submitted": True,
        "blocking_rule_ids": [],
        "needs_human_review": [],
    }


def test_preflight_and_override_never_return_raw_intake_text() -> None:
    sensitive_text = "My Aadhaar is 1234 5678 9012."
    preflight_response = client.post(
        "/preflight",
        json={"uan": "999000000002", "intake_text": sensitive_text},
    )

    assert preflight_response.status_code == 200
    preflight_body = preflight_response.text
    assert sensitive_text not in preflight_body
    assert "1234 5678 9012" not in preflight_body
    assert "123456789012" not in preflight_body
    assert "intake_text" not in preflight_response.json()

    override_response = client.post(
        "/override",
        json={"state": preflight_response.json(), "overrides": {}},
    )

    assert override_response.status_code == 200
    override_body = override_response.text
    assert sensitive_text not in override_body
    assert "1234 5678 9012" not in override_body
    assert "123456789012" not in override_body
    assert "intake_text" not in override_response.json()
