## Session 1a, 29 Aug, 1:34 AM, model: gpt-5.6-luna

Prompt: Read PLAN.md. Create `backend/models.py` with Pydantic v2 models: `MemberProfile` with the fields referenced in the PLAN.md rule table, `Severity` (BLOCKER, WARNING, INFO), `Actor` (CITIZEN, EMPLOYER, BANK),
and `RuleResult` (rule_id, severity, actor, field_read, observed_value, why,
fix, eta_days, source_note).
Then `backend/rules.py` with a `RULES` registry and exactly two rules
implemented: R01 and R03 from the PLAN.md table.
Then `backend/tests/test_rules.py` with a fires and a does-not-fire fixture
for each. Run pytest and show the output.
Output: models.py, rules.py (R01, R03), test_rules.py. 4 passing.
Corrected by me: R03 compared raw strings, so it fired on any whitespace or
case difference. Added normalization before the comparison.
Corrected by me: firing tests only asserted non-null, not rule_id. Tightened.

## Session 1b, 29 Aug, 1:16 PM , model: gpt-5.6-luna

Prompt: Each firing test must assert rule\_id, severity, field\_read and observed\_value, following the pattern now in test\_rules.py. Following the exact pattern established in `backend/rules.py`, implement R02, R04, R05, R06, R07 and R08 from the PLAN.md table. Add fires and does-not-fire fixtures for each. Run pytest.

Output: R02, R04-R08 implemented, 16 tests passing.
Checked by me: R05 guard logic confirmed correct (De Morgan, early return style). Checked by me: claim_type comparison is string literal not enum - noted, acceptable for now. 

Corrections: none needed, pattern held from 1a.

## Session 1c, 29 Aug, 2:10 PM , model: gpt-5.6-luna

Prompt: Same pattern, implement R09 through R15 from the PLAN.md table. R10 and R13 are WARNING severity, the rest are BLOCKER. Add fixtures for each. Run pytest and show me the full list of rule ids in the registry.
Output: Implemented R02, R04, R05, R06, R07, and R08 with firing/non-firing tests. Firing tests use the full assertion pattern for `rule_id`, `severity`, `field_read`, and fixture-derived `observed_value`. Also fixed the malformed `pytest.ini` so tests could run.
Checked by me: R09–R15 implementation

Corrections: none needed, pattern held from 1a.

## Session 2a, 29 Aug 2026, 2:43 PM, model: gpt-5.6-luna

Prompt: Create `backend/deps.py`. Encode the dependency edges from PLAN.md. Function `order_fixes(fired: list[RuleResult]) -> list[RuleResult]`: topological sort over the edges, blockers before warnings, and within a tier order by how many other fired rules each one unblocks, descending. Tests using stubbed RuleResults, no network.
Output: backend/deps.py with DEPENDENCIES (6 edges) and order_fixes. 33 tests passing.
Checked by me: ran pytest, 33 passed.
Reviewed by me: all 6 PLAN.md edges encoded, none invented. Three hand-traced ordering cases matched expected output. Tie-break by unblock-count confirmed correct.
Noted, not fixed: severity clause in order_fixes is unexercised by the current edge table (no warning sits upstream of a blocker). Correct defensive code, left as is.
Corrections: none.

## Session 2c, 29 Aug 2026, 2:57 PM, model: gpt-5.6-luna

Prompt: Create `backend/llm.py`, the only file importing the OpenAI SDK. Three functions: `parse_intake`, `explain_results`, `draft_message`. Each returns a validated Pydantic object using structured outputs, never free text. Each wraps its call so that a missing key or any exception returns a `degraded=True` result carrying the raw `RuleResult.why` strings instead. Add an in-process cache keyed on (rule\_ids tuple, language) for `explain_results`. Tests confirm the degraded path works with no key set.
Output: backend/llm.py with parse_intake, explain_results, draft_message. 37 tests passing. Reviewed by Claude Code (Round 5): only file importing OpenAI SDK onfirmed. Ran all three with OPENAI_API_KEY unset - all returned degraded=True with real why strings, none raised. Cache keyed on (rule_ids, language) verified. 

Corrected by me: fallback model was hardcoded gpt-4o-mini, changed to read OPENAI_MODEL env with gpt-5.6-luna default, matching .env and the budget. 

Noted, not fixed: cache only serves after a successful call (fine); draft_message forces language onto result where the other two do not (fine).

## Session 2b, 29 Aug 2026, 2:57 PM, model: gpt-5.6-Terra

Prompt: Create `backend/graph.py` with LangGraph. One Pydantic state object `PreflightState`. Nodes in fixed order: intake, clarify, resolve\_profile, run\_rules, order\_fixes, explain, verify, render. Only intake and explain touch `llm.py`. run\_rules and order\_fixes are pure. `verify` drops any sentence in the explain output whose rule\_id is not in the fired set and appends it to `state.needs_human_review`. The clarify loop is the only conditional edge, capped at one iteration. Tests with a stubbed llm module. No network, no API key.

Output: backend/graph.py, LangGraph state machine, verify node. 39 tests passing. Reviewed: node order and llm boundary confirmed. Verifier gate hand-traced: hallucinated R99 sentence dropped from output and routed to needs_human_review. Real removal, fresh allow-list, not a filter. Clarify loop capped at one iteration, schema-enforced. 

Corrected by me: PLAN.md said two clarifying questions, code does one. Aligned PLAN.md to the code.

## Session 3a, 29 Aug 2026, 3:30 PM, model: gpt-5.6-Luna

Prompt: Create `backend/voi.py`. `questions_worth_asking(profile, unknown_fields) -> list[Question]`. For each unknown field, simulate each plausible value, re-run RULES, and return the question only if at least one rule's fired status changes across those values. Cap at 1 question, ordered by how many rules flip. Tests.

Output: backend/voi.py, one-question value-of-information gate. 42 tests passing. Review: spec alignment confirmed across PLAN/AGENTS/code. Two hand-run cases: no-flip field returned nothing, flipping field returned a question citing the right rule. Simulation runs the real RULES registry, no network. Core "only ask if it flips" property has a passing test. Noted, not fixed: two of three VOI tests would survive guard deletion (the key one would not, so acceptable). N8: boolean option list skips dedup, harmless. 

Corrections: none.

## Session 3b, 29 Aug 2026, 4:15 PM, model: gpt-5.6-Luna

Prompt:Create `backend/scrub.py`. Strip any 12-digit sequence and any PAN-shaped token (5 letters, 4 digits, 1 letter) from free text before it reaches `llm.py`. Return the cleaned text plus a list of what kind of thing was stripped, so the UI can tell the citizen. Wire it into the intake node. Tests including a text with neither.
B1: In `backend/scrub.py`, the 12-digit redaction only matches a contiguous run, so "1234 5678 9012" and "1234-5678-9012" pass through unredacted. Fix the pattern to also catch 12-digit sequences separated into groups by single spaces or hyphens, while still catching the contiguous form. Do not redact legitimate longer numbers like a 14-digit reference. Then add three tests to `test_scrub.py`: a spaced Aadhaar, a hyphenated Aadhaar, and a 14-digit number that must NOT be stripped. Assert `stripped_types` for each. Run pytest.
B2: In `backend/scrub.py`, blocker B2 from REVIEW\.md Round 9: the grouped-form 12-digit pattern matches the first three groups of a longer grouped sequence, so "1234 5678 9012 3456" becomes "[REDACTED] 3456". The contiguous branch already guards this with a `(?!\d)` lookahead; the grouped alternative needs the equivalent. Add a `(?![ -]?\d)` lookahead to the grouped alternative so it only matches when the 12-digit grouped sequence is not followed by another grouped digit. Then add a test asserting "1234 5678 9012 3456" passes through untouched with empty `stripped_types`. Run pytest.
B3: In `backend/scrub.py`, blockers B2 and B3 show the grouped 12-digit regex with lookarounds is fighting itself. Replace the grouped-digit detection with a clear two-step approach instead of one regex with lookbehind/lookahead. Step one: find every maximal run of digits-and-single-separators (spaces or hyphens between digit groups). Step two: for each such run, strip the separators, and redact it only if the resulting digit string is exactly 12 digits long. A run that reduces to 16 or 20 digits is left untouched. A run that reduces to 12 is redacted regardless of what words or numbers sit before or after it, as long as they are separated by a word boundary or whitespace. Keep the contiguous-12-digit and PAN redaction as they are.
Then replace the ad-hoc tests with these cases and assert `stripped_types` for each: "123456789012" redact, "1234 5678 9012" redact, "1234-5678-9012" redact, "UAN 1000 1234 5678 9012" must redact the trailing 12-digit group, "0000-1234 5678 9012" redact the 12-digit group, "1234 5678 9012 3456" (16) untouched, "12345678901234" (14) untouched, clean text untouched. Run pytest.

Output: backend/scrub.py, redaction wired before the LLM call. 52 tests passing. Review found and I fixed, in sequence: 

B1 - spaced/hyphenated Aadhaar reached the model unredacted (all 45 tests missed it). 

B2 - grouped pattern swallowed the first 12 digits of a 16-digit sequence. 

B3 - lookbehind fix leaked a real Aadhaar when a UAN preceded it. 

Final fix rewrote grouped detection as two-step: find digit-and-separator runs, redact only runs that reduce to exactly 12 digits. B2 and B3 resolved. 

Accepted as limitation: W2, multiple leading numeric groups run together with no words between (e.g. "UAN 1000 2000 1234..."). Not a realistic free-text shape. Documented on the limitations page. A production PII service would own this.
