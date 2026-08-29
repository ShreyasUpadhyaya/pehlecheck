# Codex prompts, in order

Every prompt assumes AGENTS.md and PLAN.md are already in the repo, so none of
them restate scope. Keep it that way, it is what keeps each turn cheap.

Model column is a suggestion. Default to the smallest you have, escalate only
after two failures.

---

## Session 1, model: smallest available

### 1a. Types and two rules

> Read PLAN.md. Create `backend/models.py` with Pydantic v2 models:
> `MemberProfile` with the fields referenced in the PLAN.md rule table,
> `Severity` (BLOCKER, WARNING, INFO), `Actor` (CITIZEN, EMPLOYER, BANK),
> and `RuleResult` (rule_id, severity, actor, field_read, observed_value, why,
> fix, eta_days, source_note).
> Then `backend/rules.py` with a `RULES` registry and exactly two rules
> implemented: R01 and R03 from the PLAN.md table.
> Then `backend/tests/test_rules.py` with a fires and a does-not-fire fixture
> for each. Run pytest and show the output.

Review this one properly. The shape you approve here gets copied 13 more times.

### 1b. Rules R02, R04 to R08

> Following the exact pattern established in `backend/rules.py`, implement
> R02, R04, R05, R06, R07 and R08 from the PLAN.md table. Add fires and
> does-not-fire fixtures for each. Run pytest.

### 1c. Rules R09 to R15

> Same pattern, implement R09 through R15 from the PLAN.md table. R10 and R13
> are WARNING severity, the rest are BLOCKER. Add fixtures for each.
> Run pytest and show me the full list of rule ids in the registry.

---

## Session 2, model: mid tier

### 2a. Dependency ordering

> Create `backend/deps.py`. Encode the dependency edges from PLAN.md.
> Function `order_fixes(fired: list[RuleResult]) -> list[RuleResult]`:
> topological sort over the edges, blockers before warnings, and within a
> tier order by how many other fired rules each one unblocks, descending.
> Tests using stubbed RuleResults, no network.

### 2b. The graph

> Create `backend/graph.py` with LangGraph. One Pydantic state object
> `PreflightState`. Nodes in fixed order: intake, clarify, resolve_profile,
> run_rules, order_fixes, explain, verify, render. Only intake and explain
> touch `llm.py`. run_rules and order_fixes are pure.
> `verify` drops any sentence in the explain output whose rule_id is not in
> the fired set and appends it to `state.needs_human_review`.
> The clarify loop is the only conditional edge, capped at one iteration.
> Tests with a stubbed llm module. No network, no API key.

### 2c. The LLM boundary

> Create `backend/llm.py`, the only file importing the OpenAI SDK. Three
> functions: `parse_intake`, `explain_results`, `draft_message`. Each returns
> a validated Pydantic object using structured outputs, never free text.
> Each wraps its call so that a missing key or any exception returns a
> `degraded=True` result carrying the raw `RuleResult.why` strings instead.
> Add an in-process cache keyed on (rule_ids tuple, language) for
> `explain_results`. Tests confirm the degraded path works with no key set.

---

## Session 3, model: smallest

### 3a. Value of information

> Create `backend/voi.py`. `questions_worth_asking(profile, unknown_fields)
> -> list[Question]`. For each unknown field, simulate each plausible value,
> re-run RULES, and return the question only if at least one rule's fired
> status changes across those values. Cap at 1 question, ordered by how many
> rules flip. Tests.

### 3b. Scrubbing

> Create `backend/scrub.py`. Strip any 12-digit sequence and any PAN-shaped
> token (5 letters, 4 digits, 1 letter) from free text before it reaches
> `llm.py`. Return the cleaned text plus a list of what kind of thing was
> stripped, so the UI can tell the citizen. Wire it into the intake node.
> Tests including a text with neither.

### 3c. Data and API

> Create `backend/data/members.json` with the 5 synthetic profiles described
> in PLAN.md. UANs start with 999, names obviously fictional.
> Then `backend/main.py`: FastAPI with POST /preflight, POST /override,
> POST /draft, POST /submit-mock, and static serving of the built frontend
> from `/`. Same origin, so no CORS config.

---

## Session 4, model: smallest

### 4a. UI skeleton

> Generate `frontend/src/components/VerdictHeader.tsx` and `IssueCard.tsx`
> per `frontend/AGENTS.md`. IssueCard order is: explanation, then field and
> observed value, then actor and eta, then the "This is wrong about me"
> button. Tailwind, 360px first, no confidence scores anywhere.

### 4b. Whatever broke

One task per prompt. Name the file. Paste the traceback, not the whole repo.

---

## Session 5

Reserve. Do not plan work into it.

---

## Prompt hygiene

- One task per turn.
- Always name the file path. Never make it search the repo.
- Turn off every MCP server. You need none of them here.
- `/status` before each session to see remaining limits.
- Do not spend a turn on your own typo. Read the traceback first.
