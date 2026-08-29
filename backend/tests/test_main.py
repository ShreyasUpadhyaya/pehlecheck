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
    assert {result["rule_id"] for result in body["fired_results"]} == {"R02", "R05"}


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
    assert response.json()["fired_results"] == []


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
