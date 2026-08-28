# PehleCheck

Pre-submission rejection check for Indian government claim forms.
Demo vertical: EPF claims. Independent hackathon prototype, synthetic data only.

Read PLAN.md for scope and the rule list. Do not re-derive scope.

## Non-negotiables

- Eligibility is decided ONLY by pure functions in `backend/rules.py`.
  No model call may decide whether a citizen qualifies.
- Every user-facing sentence carries a `rule_id`. Unmapped text is dropped,
  never shown.
- All member data is synthetic. Never generate anything resembling a real
  Aadhaar number, PAN, phone number, or bank account.
- Tests run with no network and no API key. Ever.
- Never show a confidence score to a citizen.

## Stack

Backend: Python 3.11, FastAPI, LangGraph, Pydantic v2, pytest.
Frontend: Vite + React + TypeScript + Tailwind.
Not used: MongoDB, vector search, SHAP, any auth provider.

## Working style

- One task per turn. Do not refactor beyond what was asked.
- Run `pytest -q` after backend changes and report the result.
- If a requirement is ambiguous, state the assumption in one line and proceed.
  Do not ask a clarifying question unless the code cannot be written without it.
