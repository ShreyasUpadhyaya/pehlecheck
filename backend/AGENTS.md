# backend

## Layout

- `models.py`   Pydantic v2 models. Every boundary is typed.
- `rules.py`    The 15 rules and the RULES registry. Pure. No I/O.
- `deps.py`     Rule dependency DAG plus topological fix ordering.
- `voi.py`      Value-of-information gate for clarifying questions.
- `scrub.py`    Sensitive-pattern stripping before any model call.
- `graph.py`    LangGraph state machine.
- `llm.py`      The only file that imports the OpenAI SDK.
- `main.py`     FastAPI app.
- `data/members.json`  5 synthetic profiles.
- `tests/`      pytest. Hermetic.

## Contracts

- A rule is `(profile: MemberProfile) -> RuleResult | None`.
  Returns None when it does not fire. No side effects, no I/O, no clock reads.
- `RuleResult` must populate `field_read` and `observed_value` so the UI can
  show the citizen exactly what triggered it.
- LangGraph nodes take and return `PreflightState`. Fixed edges only.
  The one exception is the clarify loop, capped at a single iteration.
- Model calls live only in `llm.py`, only for intake, explanation, and drafting.
  Each returns a validated Pydantic object, never free text.
- If the model call raises or the key is missing, fall back to the raw
  `RuleResult.why` string. The app must stay usable with zero model access.

## Tests

- Every rule gets a fires fixture and a does-not-fire fixture.
- Graph tests use stubbed rule results and a fake `llm.py`.
- No `requests`, no `httpx` to a real host, no `OPENAI_API_KEY` needed.
