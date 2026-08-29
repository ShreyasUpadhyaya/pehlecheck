# REVIEW

## Round 1, 2026-08-29, reviewing 4daba1d

### Blocking
None. R01 and R03 are both correct against the PLAN.md table, and both
populate `field_read`/`observed_value` with real profile data, not
placeholders.

### Worth fixing
- [W1] `backend/tests/test_rules.py:17-27` `test_r03_fires_when_names_differ`
  never asserts on `observed_value`. It only checks `result is not None`,
  `rule_id`, and `field_read`. This test would still pass if
  `rule_r03`'s `observed_value` were hardcoded or wrong. Since you're about to
  clone this test 13 times, add an `observed_value == {...}` assertion to the
  copied fire-test so the pattern catches a hardcoded/empty observed_value
  from the start, not just an inverted condition.

### Noted, not worth your time today
- [N1] `backend/rules.py:25-28`, `:46-49` every string field (`why`, `fix`,
  `source_note`) is prefixed with `"R01: "` / `"R03: "` redundantly, since
  `rule_id` is already a separate field on `RuleResult`. Not a defect, but if
  you're copying this pattern 13 more times it's 13 more places carrying
  redundant text the UI likely already gets from `rule_id`. Your call.

### Verified working
- Ran `pytest -q` at HEAD (4daba1d): 4 passed.
- Confirmed by inspection that both rule signatures match the contract in
  `backend/AGENTS.md:18` (`(profile: MemberProfile) -> RuleResult | None`,
  pure, returns `None` when not firing).
- Confirmed both tests would fail if their rule's fire condition were
  inverted: `test_r01_fires_when_uan_is_not_activated` and
  `test_r01_does_not_fire_when_uan_is_activated` are complementary and both
  assert on the result; `test_r03_fires_when_names_differ` and
  `test_r03_does_not_fire_for_equivalent_normalized_names` are likewise
  complementary — an inverted condition on either rule flips a
  `None`/not-`None` assertion and fails.
- `field_read` values match the PLAN.md table exactly for both rules
  (`uan_activated` for R01; `name_as_per_epfo, name_as_per_aadhaar` for R03).
  `severity`, `actor`, and `eta_days` also match the table (BLOCKER/CITIZEN/1
  and BLOCKER/CITIZEN/15 respectively).

## Round 2, 2026-08-29, reviewing working tree (backend/tests/test_rules.py)

### Blocking
None.

### Worth fixing
None.

### Noted, not worth your time today
None.

### Verified working
- Ran `pytest -q backend/tests/test_rules.py`: 4 passed.
- This closes [W1] from Round 1: `test_r01_fires_when_uan_is_not_activated`
  and `test_r03_fires_when_names_differ` now assert `observed_value` against
  the actual profile value (`profile.uan_activated`, and the real
  `name_as_per_epfo`/`name_as_per_aadhaar` dict) instead of a hardcoded
  literal or nothing at all. Both also now assert `severity`, in addition to
  the existing `rule_id`/`field_read` checks. A hardcoded or wrong
  `observed_value` in a future rule would now be caught by copying this
  block.
- The `# Copy this assertion block when adding a rule.` comments correctly
  mark the fire-test bodies (not the no-fire tests, which don't need
  observed_value/severity/field_read checks) as the template for R02, R04-R15.

### Pattern verdict for the next 13 rules
Sound, with one gap to close before copying. The `RuleResult` construction
(field_read as the literal field name(s), observed_value as the actual
profile value, `None` on no-fire, single early return) is safe to replicate.
The one thing to fix in the template before cloning is the fire-test
asserting `observed_value` — do that once in R01/R03's tests (or just in
the shared test helper you write for the remaining 13), not 13 times after
the fact.

## Round 3, 2026-08-29, reviewing a88b94c

Note before the findings: the request assumes R09-R15 still need to be
written. At HEAD (`a88b94c session 1c: R09-R15, 30 tests passing`) they are
already implemented and tested, so this round reviews what already exists
rather than a pattern to extrapolate from.

### Rule-by-rule check against PLAN.md's table

All 15 rules read the field(s) the table names, fire exactly when the table
says, and carry the table's `severity`/`actor`/`eta_days`. No mismatches
found:

| id | field match | condition match | severity/actor/eta match |
|---|---|---|---|
| R01 | yes | yes | yes (BLOCKER/CITIZEN/1) |
| R02 | yes | yes | yes (BLOCKER/EMPLOYER/7) |
| R03 | yes | yes | yes (BLOCKER/CITIZEN/15) |
| R04 | yes | yes | yes (BLOCKER/CITIZEN/15) |
| R05 | yes | yes (`date_of_exit is not None or claim_type != FINAL_SETTLEMENT` correctly de-Morgans to "fires when exit date null AND type is FINAL_SETTLEMENT") | yes (BLOCKER/EMPLOYER/10) |
| R06 | yes | yes | yes (BLOCKER/BANK/3) |
| R07 | yes | yes ("differ, or account is joint") | yes (BLOCKER/CITIZEN/5) |
| R08 | yes | yes | yes (BLOCKER/CITIZEN/3) |
| R09 | yes | yes (`<6` and `PENSION_WITHDRAWAL`) | yes (BLOCKER/CITIZEN/0) |
| R10 | yes | yes (`<60` and amount strictly `>` threshold, matching "above") | yes (WARNING/CITIZEN/1) |
| R11 | yes | yes | yes (BLOCKER/CITIZEN/60) |
| R12 | yes | yes (`>1` member_ids and any untransferred) | yes (BLOCKER/CITIZEN/20) |
| R13 | yes | yes (eps months `<` service months) | yes (WARNING/EMPLOYER/15) |
| R14 | yes | yes (amount `>` purpose limit; unmapped `claim_purpose` correctly does not fire) | yes (BLOCKER/CITIZEN/0) |
| R15 | yes | yes (`claim_purpose` not in the set for `claim_type`) | yes (BLOCKER/CITIZEN/0) |

### Test strength: fire-condition inversion

For each rule, negating the early-return guard (so the rule fires exactly
opposite of today) flips at least one of the fixture's two tests from pass to
fail, for all 15 rules. The boolean-field rules (R01, R02, R06, R08) invert
directly. The comparison rules use fixtures placed exactly at the boundary
(R10: 59/60 months, 50000/50001 amount; R13: 11/12 vs 12/12; R14: 100000 vs
100001), so a `<`/`<=` or `>`/`>=` flip is also caught, not just a full
condition negation.

### Test strength: assertions on rule_id/severity/field_read/observed_value

Every one of the 15 firing tests asserts all four
(`rule_id`, `severity`, `field_read`, `observed_value`), and every
`observed_value` assertion compares against the fixture's actual attribute(s)
(e.g. `profile.uan_activated`, or a dict built from `profile.x`), never a
repeated/hardcoded literal independent of the fixture. This is the Round 2 fix
applied consistently across all 15 rules, not just R01/R03.

### claim_type: enum or raw string?

Raw string, consistently. `MemberProfile.claim_type` (`backend/models.py:40`)
is typed `str`, not an enum — unlike `Severity`/`Actor`, which are
`StrEnum`s in the same file. Every rule that reads it (R05, R09, R11, R15)
and `CLAIM_PURPOSES`'s keys (`backend/rules.py:17-21`) compares it against
plain string literals (`"FINAL_SETTLEMENT"`, `"PENSION_WITHDRAWAL"`). Same
story for `claim_purpose`: plain `str` field, compared/keyed against literal
strings in R14/R15. Usage is internally consistent — no rule treats either
field as an enum while another treats it as a string — but nothing in
`MemberProfile` or Pydantic validation catches a typo'd literal
(`"FINAL_SETTLMENT"`) at the model boundary; it would just silently fail to
match in every rule that reads it. Not blocking for a hackathon build, but
worth a `StrEnum` for `claim_type`/`claim_purpose` if there's time, since
several call sites (R05, R09, R11, R15, plus `CLAIM_PURPOSES`) already depend
on exact string matches.

### Blocking
None.

### Worth fixing
None new. (See Round 1's [W1], already resolved in Round 2.)

### Noted, not worth your time today
- [N2] `backend/models.py:40` `claim_type` and `claim_purpose` are raw `str`
  fields rather than `StrEnum`s, unlike `Severity`/`Actor`. A typo in a
  literal used by `rule_r05`/`rule_r09`/`rule_r11`/`rule_r15`/
  `CLAIM_PURPOSES` would silently never fire rather than erroring. Usage is
  consistent today; flagging only because it's the kind of thing that gets
  more expensive to fix the more rules reference it, and all 15 rules are
  now in place.

### Verified working
- Ran `pytest -q` at HEAD (a88b94c): 30 passed.
- Confirmed by inspection that all 15 rules match PLAN.md's field, condition,
  severity, actor, and eta_days (table above).
- Confirmed all 15 firing tests would fail under an inverted/boundary-flipped
  fire condition, and all 15 assert `rule_id`, `severity`, `field_read`, and
  `observed_value` against the real fixture value.
- `claim_type`/`claim_purpose` comparisons are consistently raw strings
  across every rule that touches them; no enum is defined for either.

## Round 4, 2026-08-29, reviewing 7931a96

### Dependency edges: PLAN.md vs backend/deps.py

`DEPENDENCIES` (`backend/deps.py:8-15`) encodes exactly the six edges in
PLAN.md's "Dependency edges for `deps.py`" section, no more, no fewer:
R02←R08, R06←R02, R07←R02, R05←R11, R12←R01, R13←R05. Confirmed one-to-one
against PLAN.md:73-78. Nothing invented, nothing missing.

### Manual cases

Constructed by hand and run directly against `order_fixes`:

1. R08 and R02 fired (R02 depends on R08) → got `["R08", "R02"]`. Matches:
   R08 has no unfired dependency so it's ready first; R02 only becomes ready
   once R08 is placed.
2. A warning and an unrelated blocker fired together (R10 WARNING, R06
   BLOCKER, no edge between them) → got `["R06", "R10"]`. Blocker sorts
   first via `_SEVERITY_RANK` regardless of the (empty, in this case) leverage
   count. Note: I could not construct a case from PLAN.md's actual edge table
   where a BLOCKER depends on a WARNING or vice versa in a way that would
   pit "blocker priority" against "topological necessity" — every edge in
   the table has a BLOCKER as the dependency, so the two orderings (severity
   rank, dependency order) never conflict for any real fired-set. The
   `_SEVERITY_RANK` clause is exercised on ties/unrelated rules only,
   consistent with what the fixed table permits.
3. A rule with no edges fired alone (R03, which appears in `DEPENDENCIES`
   neither as key nor value) → got `["R03"]`. Trivially correct.

All three match the expected order.

### Tie-breaking by leverage (how many other fired rules a rule unblocks)

`_priority` (`backend/deps.py:25-35`) sorts ready rules by
`(severity_rank, -len(dependents[rule_id]), rule_id)`. `dependents[rule_id]`
is the set of *currently fired* rules waiting on `rule_id`, so
`-len(...)` correctly favors the rule that unblocks the most other fired
rules within the same severity tier, with `rule_id` as a final deterministic
tiebreak. This matches PLAN.md:70-71 ("within a tier, whichever unblocks the
most other rules first").

### backend/tests/test_deps.py

- All three tests use `stub()` (`backend/tests/test_deps.py:5-16`), a plain
  `RuleResult` constructor with literal fields — no network, no I/O, no
  `OPENAI_API_KEY`.
- `test_order_fixes_respects_dependencies` and
  `test_order_fixes_prioritizes_blockers_and_unblocks_most_rules` both assert
  a full ordered list (`[result.rule_id for result in order_fixes(fired)] ==
  [...]`) whose expected order differs from the input order they construct
  `fired` in. If `order_fixes` were replaced with the identity function (sort
  removed entirely), both would fail — they are asserting order, not just
  membership.
- `test_order_fixes_treats_unfired_dependencies_as_satisfied` passes a
  single-element list and asserts `order_fixes(fired) == fired`. This one
  would still pass under an identity `order_fixes` — a single-element list
  is already in its own order regardless of sorting logic. That's fine as a
  test of the "unfired dependencies don't block" behavior (its actual
  purpose), but it contributes nothing to catching a removed/broken sort;
  the other two tests are what carry that.

### Blocking
None.

### Worth fixing
None.

### Noted, not worth your time today
- [N3] `backend/tests/test_deps.py:51-54` as above:
  `test_order_fixes_treats_unfired_dependencies_as_satisfied` can't detect a
  missing sort by itself. Not asking for a change — the other two ordering
  tests already cover that — just noting it so it's not mistaken for
  evidence of sort-order coverage on its own.

### Verified working
- Ran `pytest -q` at HEAD (7931a96): 33 passed.
- Confirmed `DEPENDENCIES` is exactly PLAN.md's six edges by direct
  comparison.
- Ran the three hand-constructed cases directly against `order_fixes`;
  output matched expectations for all three (shown above).
- Confirmed by inspection that two of the three `test_deps.py` tests assert
  full order and would fail if sorting were removed; the third would not,
  but tests a different property (unfired deps treated as satisfied).

## Round 5, 2026-08-29, reviewing e0fd3c0

### Correction to the request's premise

The request asks me to confirm the fallback model is `gpt-5.6-luna`. It
isn't — `backend/llm.py:12` is
`_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")`. `gpt-4o-mini` is the
fallback, read from `OPENAI_MODEL` with that as default, which is otherwise
exactly what was asked (env-var-first, sane fallback). Reporting what's
actually in the file rather than confirming the premise as given.

### Only file importing the OpenAI SDK

Confirmed: `grep -r "import openai\|from openai"` across the repo matches
only `backend/llm.py:6`.

### All three functions return validated Pydantic objects

`IntakeResult`, `ExplanationResult`, `DraftMessageResult`
(`backend/llm.py:16-44`) are all `BaseModel` subclasses with
`extra="forbid"`. `parse_intake`, `explain_results`, and `draft_message` each
return one of these on both the success and except path — no function
returns a bare string anywhere.

### Degraded path — actually run, not reasoned about

Ran all three with `OPENAI_API_KEY` popped from the environment
(`os.environ.pop("OPENAI_API_KEY", None)`), no `monkeypatch`, real
`_structured_call` code path:

- `parse_intake(...)` → `degraded=True language='en' claim_type=None
  claim_purpose=None clarifying_question=None
  rule_whys=['R01: raw why']` — no exception raised.
- `explain_results(...)` → `degraded=True language='en' sentences=[]
  rule_whys=['R01: raw why one', 'R02: raw why two']` — no exception raised.
- `draft_message(...)` → `degraded=True language='en'
  recipient=<Actor.EMPLOYER: 'EMPLOYER'> message=''
  rule_whys=['R01: raw why one', 'R02: raw why two']` — no exception raised.

All three carry the raw `RuleResult.why` strings via `rule_whys`, all three
set `degraded=True`, none raised. This matches `backend/AGENTS.md`'s
"fall back to the raw `RuleResult.why` string" contract.

### explain_results cache

Keyed on `(tuple(rule_id for rule_id in results), language)`
(`backend/llm.py:102`), matching the "keyed by rule_ids and language"
requirement. Confirmed two ways:
- Live (no key): calling `explain_results` twice with the same rule set
  leaves `llm._EXPLANATION_CACHE` at size 0 — see next section, this is a
  real behavior worth flagging, not a bug in the cache key itself.
- `test_explain_results_cache_is_keyed_by_rule_ids_and_language`
  (`backend/tests/test_llm.py:45-59`) monkeypatches `_structured_call`
  itself and asserts `first is second` plus `len(calls) == 1` after two
  calls with an identical key — this does verify no second "API" call
  happens on a cache hit, and does so hermetically.

One behavior worth flagging, not blocking: the cache is only populated on
the success path (`backend/llm.py:114-115`); the `except` branch
(`backend/llm.py:117-122`) returns a fresh degraded `ExplanationResult`
without touching `_EXPLANATION_CACHE`. So with no API key, repeated calls to
`explain_results` with the same `(rule_ids, language)` never hit the cache —
each call re-enters `_structured_call`, which fails fast on the missing key
(no network attempted), so there's no cost today, but it means "does a
repeat call with the same key hit the API" is really only false because the
call fails before reaching the network, not because the cache is serving it.
If a key is later configured and a transient failure degrades one call, the
next identical call retries the network rather than reusing the degraded
result — that's probably fine (you'd want to retry, not cache a failure),
just flagging so it's a deliberate choice rather than an accident.

### Tests: no key, no network

`backend/tests/test_llm.py` needs neither. The three degrade tests use
`monkeypatch.delenv("OPENAI_API_KEY", raising=False)`, which drives the real
`_structured_call` to raise `RuntimeError` before constructing an `OpenAI`
client, so no network is attempted. The cache test monkeypatches
`_structured_call` directly, so it never touches the real OpenAI SDK or
network either.

### Blocking
None.

### Worth fixing
None.

### Noted, not worth your time today
- [N4] `backend/llm.py:91` `parse_intake`'s success path does
  `result.model_copy(update={"degraded": False, "rule_whys": []})` without
  forcing `language` to the caller's requested `language`, unlike
  `draft_message` (`backend/llm.py:139-141`), which does force `language`
  and `recipient` on its success path. `explain_results`
  (`backend/llm.py:114`) is the same as `parse_intake` — no forced
  `language`. If the model ever returns a different `language` value than
  requested, `parse_intake`/`explain_results` would silently pass it
  through while `draft_message` would not. Inconsistent, not obviously
  wrong, and not something you'll see with the seeded demo data — noting in
  case it produces a confusing UI mismatch during the video.
- [N5] `backend/llm.py:117-122` `explain_results`'s except branch never
  writes to `_EXPLANATION_CACHE` (see above) — degraded results are never
  cached, only successful ones. Consistent with "don't cache failures," but
  means the cache guarantee only kicks in once a key is configured and a
  call succeeds. No action needed unless you want degraded calls memoized
  too.

### Verified working
- Ran all three functions directly with `OPENAI_API_KEY` unset (not
  `monkeypatch`, actual `os.environ`): all three returned `degraded=True`
  with real `rule_whys` from the fixtures, none raised (output above).
- Confirmed `backend/llm.py` is the only file in the repo importing the
  OpenAI SDK.
- Confirmed all three public functions return Pydantic model instances on
  both branches.
- Confirmed the cache is keyed on `(rule_ids, language)` and a same-key
  repeat call does not invoke `_structured_call` again, via the existing
  monkeypatched test.
- Ran `pytest -q` at HEAD (e0fd3c0): 37 passed.

## Round 6, 2026-08-29, reviewing b82ee36

### Spec note before the findings

PLAN.md's citizen journey (PLAN.md:23) says "Answer at most **two**
clarifying questions." `backend/AGENTS.md:23` says the clarify loop is
"capped at **a single** iteration," and that's what `backend/graph.py`
implements (`clarification_loops: int = Field(..., le=1)`,
`test_graph_clarification_loop_runs_once`). Per CLAUDE.md, the spec wins
over code where they disagree — but here the two spec files disagree with
each other. Flagging per CLAUDE.md's "if the spec is itself wrong, say so
explicitly": PLAN.md and backend/AGENTS.md need to agree on one vs. two
clarifying questions; right now the code matches AGENTS.md, not PLAN.md.

### Node order and LLM boundary

`build_graph()` (`backend/graph.py:145-169`) wires exactly:
`intake → clarify → (loop once) → resolve_profile → run_rules →
order_fixes → explain → verify → render`, matching the citizen-journey
sequence (describe → clarify → verdict → issue cards). `grep "llm\." backend/graph.py`
shows only `intake` (`graph.py:47`, `llm.parse_intake`) and `explain`
(`graph.py:109`, `llm.explain_results`) reach into `llm.py`; `resolve_profile`,
`run_rules`, `order_fixes`, `verify`, and `render` do not import or call
anything from `llm`.

### run_rules / order_fixes purity

`run_rules` (`backend/graph.py:85-94`) only calls `rule(state.profile)` for
each rule in `RULES` — pure functions already reviewed in Round 3.
`order_fixes` (`backend/graph.py:97-103`) only calls
`order_rule_fixes` (`deps.order_fixes`, reviewed in Round 4) — also pure. No
model calls, no I/O, no clock reads in either node.

### The verifier gate — constructed by hand and run directly

Called `verify()` directly (not through the compiled graph) with one fired
result (`R01`) and an `ExplanationResult` containing two sentences: one
citing `R01` (fired) and one citing `R99` (not in the fired set):

```
verified_sentences: ['R01: Your UAN is not activated.']
needs_human_review: ['R99: This rule was never fired but the model hallucinated it.']
```

The `R99` sentence is **not** present in `verified_sentences` in any form.
How the drop is implemented (`backend/graph.py:113-133`): `verify` builds
`verified_sentences` as a **new, empty list** and only `.append()`s a
sentence into it when `sentence_rule_ids and sentence_rule_ids <= fired_ids`
holds (all rule IDs the sentence cites are a subset of the fired set); every
other sentence is appended to `needs_human_review` instead, in the same
loop. It is not a filter applied after the fact, not a logged warning with
the sentence left in place, and not a partial edit of the string — the
unmapped sentence is simply never added to the citizen-facing list, full
stop. `render()` (`backend/graph.py:136-142`) then sets
`rendered_sentences = state.verified_sentences` directly, so nothing
downstream of `verify` can reintroduce the dropped sentence. A sentence with
zero rule-ID matches at all is also caught by the same branch (empty set is
falsy), consistent with `backend/AGENTS.md`'s "every user-facing sentence
carries a rule_id... unmapped text is dropped, never shown."

Also confirmed via the existing test
`test_graph_runs_fixed_nodes_and_filters_unfired_explanations`
(`backend/tests/test_graph.py:38-63`), which drives the same scenario
end-to-end through the compiled graph with a stubbed LLM and asserts the
same split.

### Clarify loop bound

Traced two full passes through `clarify`: pass 1 (`clarification_loops==0`,
question set) sets `clarification_loops=1`,
`clarification_loop_pending=True`, and `_after_clarify` routes back to
`clarify`. Pass 2 now has `clarification_loops==1`, so `should_loop` is
`False` **unconditionally** — it no longer depends on whether a clarifying
question is still present — so `clarification_loop_pending` becomes `False`
and `_after_clarify` routes to `resolve_profile`. There is no path back to
`clarify` a third time: the loop guard is `loops == 0`, and `loops` only
ever increments by 0 or 1 per visit and is schema-capped at `le=1`
(`backend/graph.py:29`), which would raise a validation error as a second
line of defense if the loop guard logic were ever broken. Confirmed via
`test_graph_clarification_loop_runs_once`
(`backend/tests/test_graph.py:66-81`): `node_history.count("clarify") == 2`
(one loop-back, not more) and `clarification_loops == 1`.

### Blocking
None.

### Worth fixing
None.

### Noted, not worth your time today
- [N6] See "Spec note" above — PLAN.md says two clarifying questions,
  backend/AGENTS.md and the code say one. Worth a one-line fix to whichever
  document is wrong so the two don't keep disagreeing, but not a code
  defect.
- [N7] `backend/AGENTS.md:22` says "LangGraph nodes take and return
  `PreflightState`," but every node in `backend/graph.py` returns
  `dict[str, object]` (a partial-state update dict), not a `PreflightState`
  instance — standard LangGraph node style, and the compiled graph merges
  these correctly (confirmed by both graph tests round-tripping through
  `PreflightState.model_validate`). Not a defect, just imprecise wording in
  the contract if anyone reads it literally as "returns a full state
  object."

### Verified working
- Ran `pytest -q` at HEAD (b82ee36): 39 passed.
- Confirmed node order matches the citizen journey and that only
  `intake`/`explain` call into `llm.py`.
- Confirmed `run_rules`/`order_fixes` are pure by inspection (already-purity-
  reviewed callees, no other imports used).
- Constructed the unmapped-`rule_id` case by hand, called `verify()`
  directly, and confirmed the `R99` sentence is dropped from
  `verified_sentences` and appended to `needs_human_review` via a genuine
  list-construction filter, not a logged pass-through.
- Traced the clarify loop through two node visits and confirmed no third
  visit is reachable; corroborated by the existing loop test.

## Round 7, 2026-08-29, reviewing 6332e35

### Spec alignment (follow-up to Round 6's N6)

Confirmed: PLAN.md:22 now reads "Answer at most **one** clarifying
question," matching `backend/AGENTS.md`'s "capped at a single iteration"
and the code's cap of 1. The commit title (`docs: align PLAN clarify count
to code (one question)`) confirms this was the intended fix. No remaining
disagreement between the two spec files.

### Two hand-built cases, run directly against backend/voi.py

Case 1 — a field that cannot flip any rule: `account_is_joint=True` already
makes R07 fire unconditionally, since R07's condition is "names differ **or**
account is joint" (`backend/rules.py:136`) — so varying
`account_holder_name` on that profile can never change R07's fired status,
and no other rule reads `account_holder_name`.

```python
profile1 = MemberProfile(account_is_joint=True, name_as_per_epfo="Asha Demo", account_holder_name="Asha Demo")
_question_for_field(profile1, "account_holder_name")   # -> None
questions_worth_asking(profile1, ["account_holder_name"])  # -> []
```

Ran it: got `None` from `_question_for_field` and `[]` from
`questions_worth_asking`. No question returned, as expected.

Case 2 — a field whose value does flip a rule: `uan_activated=True` (R01
fires only when this is `False`).

```python
profile2 = MemberProfile(uan_activated=True)
_question_for_field(profile2, "uan_activated")
# -> field='uan_activated' prompt='R01: What is the uan activated?'
#    options=[True, False, True] rule_ids=['R01'] flip_count=1
questions_worth_asking(profile2, ["uan_activated"])
# -> [Question(field='uan_activated', ..., flip_count=1)]
```

Ran it: got a `Question` in both cases, correctly citing `R01` and
`flip_count=1`.

### Cap and ranking

`questions_worth_asking` (`backend/voi.py:120-133`) sorts candidates by
`(-question.flip_count, question.field)` then slices `[:1]` — cap is exactly
one, ranked by flip count descending, with the field name as a deterministic
tiebreak. Matches PLAN.md (now one question) and "ranking is by number of
rules flipped, descending."

### Simulation uses the real RULES registry, no network, no key

`_fired_ids` (`backend/voi.py:83-88`) iterates `RULES.items()` imported
directly from `backend/rules.py:10` (`from .rules import RULES, ...`) — the
same registry `run_rules` uses in the graph, not a hardcoded subset.
`backend/voi.py` imports only `datetime`, `decimal`, `typing`, `pydantic`,
and `.models`/`.rules` — no `llm`, `openai`, `requests`, `httpx`, or
`os.getenv` anywhere in the file. No network calls, no API key needed.

### Test strength: does removing the "only ask if it flips" guard break any test?

Only one of the three tests in `backend/tests/test_voi.py` actually
exercises this property:

- `test_questions_worth_asking_returns_rule_changing_question` and
  `test_questions_worth_asking_caps_at_one_and_ranks_by_flips` both use
  fields that genuinely flip a rule. If the guard in `_question_for_field`
  (`backend/voi.py:106-107`, `if not flipped_rule_ids: return None`) were
  deleted so a `Question` were always returned once ≥2 options exist, both
  of these tests would **still pass** — nothing in them distinguishes
  "returned because it flips" from "returned unconditionally," since their
  fixtures happen to flip rules either way.
- `test_questions_worth_asking_omits_fields_that_change_no_rule`
  (`backend/tests/test_voi.py:35-41`) is the one that matters here. Its
  profile has `claim_type=""` and default `claim_amount=Decimal("0")`, and
  asks about `claim_purpose` (which has ≥2 plausible options — verified by
  inspection of `_CLAIM_PURPOSES`). `claim_purpose` never flips any rule for
  this profile: R15's `CLAIM_PURPOSES.get(claim_type)` is `None` for
  `claim_type=""` so R15 never fires regardless of `claim_purpose`, and
  R14's `claim_amount=0` never exceeds any `PURPOSE_LIMITS` value regardless
  of `claim_purpose`. So this profile is a genuine no-flip case with real
  candidate options, not just an empty option list. If the guard were
  removed, this test's `assert questions == []` would fail, since a
  `Question` for `claim_purpose` would be returned. This is the one test
  that actually proves the "only ask if it flips" property.

### Blocking
None.

### Worth fixing
None.

### Noted, not worth your time today
- [N8] `backend/voi.py:52` boolean fields' plausible-value list is
  `[current, False, True]` without going through `_unique(...)` like every
  other branch in `_plausible_values` — for `uan_activated=True` this
  produces `options=[True, False, True]` with a duplicate `True`, visible in
  the case 2 output above. Doesn't affect flip detection or the cap/ranking
  (duplicates don't change `_fired_ids` results), and doesn't currently
  break any test, but it's inconsistent with the rest of the function and
  would show a citizen a duplicated option in the `options` list on the
  clarify screen.

### Verified working
- Ran `pytest -q` at HEAD (6332e35): 42 passed.
- Ran both hand-constructed cases directly against `voi.py`'s public and
  private functions — no-flip case returned no question, flip case returned
  a question citing the correct rule and flip count (output above).
- Confirmed the cap (`[:1]`) and sort key (`-flip_count`, then `field`) by
  reading `questions_worth_asking`.
- Confirmed `_fired_ids` iterates the real `backend.rules.RULES` dict
  (import traced to `backend/rules.py`), and that `backend/voi.py` has no
  network, `llm`, or API-key-related imports.
- Confirmed by inspection that only
  `test_questions_worth_asking_omits_fields_that_change_no_rule` would fail
  if the "only ask if it flips a rule" guard were deleted; the other two
  tests would pass either way.

## Round 8, 2026-08-29, reviewing 5952908

### Five cases, run directly against backend/scrub.py

```
run          '123456789012'                                     -> '[REDACTED]'                                            stripped_types=['12-digit sequence']
spaced       '1234 5678 9012'                                    -> '1234 5678 9012'  (UNCHANGED)                           stripped_types=[]
hyphenated   '1234-5678-9012'                                    -> '1234-5678-9012'  (UNCHANGED)                           stripped_types=[]
pan_lower    'abcde1234f'                                        -> '[REDACTED]'                                            stripped_types=['PAN-shaped token']
mid_sentence 'My Aadhaar is 123456789012 please verify it today.' -> 'My Aadhaar is [REDACTED] please verify it today.'      stripped_types=['12-digit sequence']
```

Cases 1, 4, and 5 pass. Cases 2 and 3 do not: the space- and hyphen-broken
12-digit sequences are returned completely unredacted, with an empty
`stripped_types`. This is the exact requirement CLAUDE.md calls out by name
("Does `backend/scrub.py` catch a 12-digit sequence with spaces or hyphens
in it, not only a clean run of digits") — it does not.

Root cause: `_SENSITIVE_TOKEN` (`backend/scrub.py:15-17`) is
`r"(?<!\d)\d{12}(?!\d)|..."` — it only matches a *contiguous* run of exactly
12 digit characters. A space or hyphen inside the sequence breaks the match
into shorter digit runs (`1234`, `5678`, `9012`), none of which is 12 digits
long, so the whole regex alternative never fires. `"1234 5678 9012"` and
`"1234-5678-9012"` both reach `llm.parse_intake` completely intact through
the `intake` node's real scrub call — confirmed separately below.

### Wiring: scrub before parse_intake

Traced `intake()` (`backend/graph.py:47-58`) directly:

```python
def intake(state: PreflightState) -> dict[str, object]:
    scrubbed = scrub_text(state.intake_text)          # scrub runs first
    result = llm.parse_intake(scrubbed.cleaned_text, ...)  # only cleaned_text is passed on
    return {"scrubbed_text": scrubbed.cleaned_text, "stripped_types": scrubbed.stripped_types, ...}
```

`state.intake_text` (the raw text) is never passed to `llm.parse_intake` —
only `scrubbed.cleaned_text` is. The order is correct: scrub happens, then
and only then does the LLM call receive the result of scrubbing. This is
confirmed by the existing `test_intake_node_sends_only_cleaned_text_to_llm`
(`backend/tests/test_scrub.py:21-39`), which stubs the LLM and asserts the
stub only ever received `"Synthetic [REDACTED] [REDACTED] claim."` — but
that test only exercises the clean-run case (`123456789012`), not the
spaced/hyphenated case from Round 8's cases 2/3, so it does not catch the
gap above. Because of that gap, a spaced or hyphenated Aadhaar number typed
by a citizen **does** reach `llm.parse_intake` verbatim through this exact
wiring — the wiring is correct, but has nothing to redact when the pattern
match fails.

### False positives and clean pass-through

Ran a 14-digit reference number and a clean sentence directly:

```
long number -> 'Reference number 12345678901234 is on file.' (unchanged) stripped_types=[]
clean       -> 'My UAN is not activated and my claim was rejected.' (unchanged) stripped_types=[]
```

Both pass through untouched with an empty `stripped_types`, as expected. The
`(?<!\d)` / `(?!\d)` lookaround boundaries correctly prevent a legitimate
14-digit number from being mistaken for (or partially swallowed as) a
12-digit Aadhaar-shaped sequence — no false positive here.

### Blocking
- [B1] `backend/scrub.py:15-17` `_SENSITIVE_TOKEN` does not match a 12-digit
  sequence broken by spaces or hyphens (`"1234 5678 9012"`,
  `"1234-5678-9012"`), so those forms of an Aadhaar number pass through
  `scrub_text` — and therefore through `intake()` into
  `llm.parse_intake` — completely unredacted. This is the specific defect
  CLAUDE.md's review checklist names explicitly for this file. Fix: strip
  separators (or make them optional in the pattern) before/while matching
  the 12-digit run, e.g. match `\d(?:[ -]?\d){11}` instead of a bare
  `\d{12}`, and redact the original matched span (not just the digits) so
  the separators are removed too.

### Worth fixing
None beyond B1.

### Noted, not worth your time today
- [N9] `backend/tests/test_scrub.py` has no case for a spaced or hyphenated
  sequence, at any of the three call sites tested (`scrub_text` directly,
  and the intake-node wiring test). Once B1 is fixed, add one so this
  doesn't regress — the existing tests would not have caught it before now
  and won't catch a regression either.

### Verified working
- Ran `pytest -q` at HEAD (5952908): 45 passed (none of these tests exercise
  the spaced/hyphenated gap, consistent with B1 above).
- Ran all five requested cases directly against `scrub_text`; output shown
  above.
- Traced `intake()` and confirmed `scrub_text` runs before
  `llm.parse_intake`, and that only `scrubbed.cleaned_text` (never
  `state.intake_text`) is passed to the LLM call — correct order, but see
  B1 for what fails to get scrubbed in the first place.
- Ran a 14-digit number and a clean sentence through `scrub_text` directly:
  both passed through unchanged with `stripped_types == []`, confirming no
  false positive on a longer legitimate number and clean pass-through for
  text with nothing sensitive in it.

## Round 9, 2026-08-29, reviewing e173d92 — re-verify of Round 8's B1

### Requested cases, run directly against backend/scrub.py

```
'123456789012'                         -> '[REDACTED]'                              stripped_types=['12-digit sequence']
'1234 5678 9012'                       -> '[REDACTED]'                              stripped_types=['12-digit sequence']
'1234-5678-9012'                       -> '[REDACTED]'                              stripped_types=['12-digit sequence']
'12345678901234' (14 digits)           -> '12345678901234'  (UNCHANGED)             stripped_types=[]
'my number is 1234 5678 9012 please'   -> 'my number is [REDACTED] please'          stripped_types=['12-digit sequence']
```

Cases 1, 2, 3, and 5 redact correctly and record
`stripped_types == ['12-digit sequence']`. Case 4 (14 contiguous digits)
passes through completely unchanged with `stripped_types == []`, as
required. All five match what was asked.

### 16-digit grouped sequence — requested boundary check

Ran `'1234 5678 9012 3456'` (four groups of four, 16 digits total) directly:

```
'1234 5678 9012 3456' -> '[REDACTED] 3456' stripped_types=['12-digit sequence']
```

This does **not** pass through untouched. The grouped-form alternative in
`_SENSITIVE_TOKEN` (`backend/scrub.py:16`) —
`\d{4}(?P<aadhaar_separator>[ -])\d{4}(?P=aadhaar_separator)\d{4}` — has no
lookahead preventing a fourth `separator + 4-digit` group from following,
unlike the plain 12-digit alternative right next to it, which does have
`(?!\d)` to reject exactly this kind of longer sequence. So the regex
matches the *first three* groups of the 16-digit input and redacts them,
leaving `" 3456"` behind as a dangling fragment — a partial, silent
mangling of a longer number rather than either "leave it alone" or "flag
the whole thing." The reported `stripped_types` also claims a clean
"12-digit sequence" was found, which isn't accurate to what actually
happened (12 of 16 digits, chosen only because they happened to come first).

### Is B1 resolved?

Partially. The specific defect Round 8 raised — a spaced or hyphenated
12-digit Aadhaar number passing through completely unredacted — is fixed;
all four of the original failing/regressed cases now redact correctly, and
`test_scrub_text` (see below) covers this. But the fix introduced a new,
narrower gap that the grouped-form alternative isn't anchored the way the
contiguous-digit alternative is, so a longer grouped digit sequence (16
digits, and by the same logic 20, 24, ...) gets its first 12 digits
silently swallowed instead of being left alone. Given this is exactly the
boundary case the request asked me to check, and it fails, I'm not marking
this round's finding as fully resolved without qualification — see [B2]
below.

### Tests

Checked `backend/tests/test_scrub.py` for coverage of the spaced/hyphenated
cases fixed in this commit — present and passing (`pytest -q`, below). No
test in the file exercises a grouped sequence longer than 12 digits (16 or
more), so nothing currently catches the gap in the previous section.

### Blocking
- [B2] `backend/scrub.py:16` the grouped-form branch of `_SENSITIVE_TOKEN`
  (`\d{4}[ -]\d{4}[ -]\d{4}` via the backreference) has no equivalent of the
  contiguous branch's `(?!\d)` boundary check, so it matches and redacts the
  first three groups of a longer grouped digit sequence (confirmed: 16
  digits grouped as 4-4-4-4 → first 12 redacted, last 4 left as a dangling
  `" 3456"` fragment) instead of leaving it alone. Fix: require the match
  not be followed by another `separator + digit` group, e.g. add
  `(?!\s?\d)` or `(?![ -]\d)` after the grouped alternative, mirroring the
  `(?!\d)` already used on the contiguous-digit alternative.

### Worth fixing
None beyond B2.

### Noted, not worth your time today
- [N10] `backend/scrub.py:26-34` when the grouped-form match above fires,
  `stripped_types` reports `"12-digit sequence"`, which is only true of the
  substring that got matched, not of what was actually in the source text
  (16 digits). Once B2 is fixed this stops being observable, so no separate
  action needed beyond the B2 fix.

### Verified working
- Ran `pytest -q` at HEAD (e173d92): 48 passed.
- Ran all five requested cases directly against `scrub_text`: cases 1, 2, 3,
  5 redact with `stripped_types == ['12-digit sequence']`; case 4 (14
  digits) passes through unchanged with `stripped_types == []` — all as
  required.
- Ran the 16-digit grouped case directly: it does **not** pass through
  untouched — the first three groups (12 of 16 digits) are redacted, per
  [B2] above.
