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

## Round 10, 2026-08-29, reviewing b0881b2 — review of the B2 fix

### The change

```diff
- r"(?<!\d)(?:\d{12}|\d{4}(?P<aadhaar_separator>[ -])\d{4}(?P=aadhaar_separator)\d{4})(?!\d)"
+ r"(?<!\d)(?:\d{12}(?!\d)|(?<!\d{4}[ -])\d{4}(?P<aadhaar_separator>[ -])\d{4}(?P=aadhaar_separator)\d{4}(?![ -]?\d))"
```

Adds a leading `(?<!\d{4}[ -])` lookbehind and a trailing `(?![ -]?\d)`
lookahead to the grouped-form alternative, plus a matching test
(`test_scrub_text_does_not_redact_longer_spaced_digit_sequence`,
`backend/tests/test_scrub.py:42-47`).

### Round 9's specific case: fixed

Re-ran `'1234 5678 9012 3456'` and a 20-digit variant directly: both now
pass through **completely unchanged** with `stripped_types == []`. The
trailing lookahead does its job. Also re-ran all five of Round 9's original
cases (contiguous, spaced, hyphenated, 14-digit, mid-sentence) — all still
behave correctly; `pytest -q` at HEAD (b0881b2): 49 passed.

### New regression introduced by the leading lookbehind

The leading `(?<!\d{4}[ -])` is separator-agnostic and content-agnostic: it
blocks a match whenever *any* 4 digits followed by a space or hyphen
immediately precede the candidate Aadhaar-shaped group — regardless of
whether that preceding text is actually part of the same number. This
causes a genuine spaced Aadhaar number to go **completely unredacted** when
another 4-digit token happens to sit directly in front of it with one
separator character, which is a realistic way for citizen free text to read
(a UAN or employee code stated right before an Aadhaar number). Ran
directly:

```
'UAN 1000 1234 5678 9012'                                -> unchanged, stripped_types=[]   (the genuine Aadhaar '1234 5678 9012' is not redacted)
'0000-1234 5678 9012'                                     -> unchanged, stripped_types=[]   (same failure, hyphen-separated lead-in)
```

For comparison, the same Aadhaar number redacts fine when nothing precedes
it directly, or when a non-digit word separates it from the preceding
number:

```
'My employee code is 1000 and Aadhaar is 1234 5678 9012'  -> '...and Aadhaar is [REDACTED]'  stripped_types=['12-digit sequence']
```

So the false negative is specifically triggered by *adjacency* — a
4-digit-plus-separator token immediately before the real Aadhaar group,
with no intervening word — which is exactly the shape of "reference numbers
mentioned back to back" that a citizen describing their claim is likely to
produce. This is a worse failure mode than Round 9's B2 (a false positive
that only leaves a fragment behind): here a real 12-digit Aadhaar number
reaches `llm.parse_intake` completely unredacted.

### Blocking
- [B3] `backend/scrub.py:16` the grouped-form alternative's leading
  `(?<!\d4}[ -])` lookbehind (typo aside — it's `\d{4}[ -]`) suppresses a
  match whenever any 4-digit-plus-separator token immediately precedes a
  genuine spaced/hyphenated 12-digit Aadhaar sequence, even when the
  preceding token is unrelated (a different number, different separator,
  no shared structure). Confirmed: `'UAN 1000 1234 5678 9012'` and
  `'0000-1234 5678 9012'` both leave a real Aadhaar-shaped
  `'1234 5678 9012'` completely unredacted. This regressed the exact
  property Round 8/9 were verifying — that no Aadhaar-shaped string reaches
  the model — for a realistic input shape. A boundary check meant to stop
  over-matching into a *longer run of the same grouped number* is instead
  keying off "any preceding digit run," which is too broad. Fixing the
  16-/20-digit false positive from Round 9 without reintroducing this needs
  the lookbehind (and lookahead) to only reject when the adjacent group
  shares the *same* separator as the candidate match, not any separator —
  e.g. checking that the character immediately before the match isn't the
  same separator character the match itself uses, or capturing one
  additional group on each side and validating separator identity, rather
  than a blanket `\d{4}[ -]`/`[ -]?\d` boundary.

### Worth fixing
None beyond B3.

### Noted, not worth your time today
- [N11] No test in `backend/tests/test_scrub.py` currently covers a
  legitimate Aadhaar number immediately adjacent to another digit group
  (the case B3 describes), which is why 49/49 tests pass despite the
  regression. Worth a case here once B3 is fixed, alongside the existing
  16-digit test, so this boundary doesn't flip back and forth again.

### Verified working
- Ran `pytest -q` at HEAD (b0881b2): 49 passed.
- Re-ran all of Round 9's cases (1-5) plus the 16-digit and a 20-digit
  grouped sequence: the Round 9 finding (B2, over-matching into longer
  grouped sequences) is resolved — both now pass through completely
  unchanged.
- Found and confirmed a new false negative (B3) by constructing realistic
  adjacent-number text and running it directly against `scrub_text`; output
  shown above.

## Round 11, 2026-08-29, reviewing f6a9556 — review of the B3 fix

### The change

The grouped-digit path was rewritten from a single regex with lookarounds
into a two-step pass: `_GROUPED_DIGIT_RUN` (`backend/scrub.py:19`) finds any
run of `\b\d+(?:[ -]\d+)+\b` first, then `replace_grouped`
(`backend/scrub.py:31-52`) decides in Python whether/how much of that run to
redact — either the whole run (if the concatenated digits total exactly 12)
or, for the specific 4-groups-of-4 shape, just the trailing three groups
when a same-separator/prefix-boundary heuristic suggests the leading group
is a different number. The contiguous-digit and PAN regex are unchanged.

### Round 9 and Round 10's specific cases: both fixed

Re-ran every case from both prior rounds directly against `scrub_text`:

```
'123456789012'                                            -> '[REDACTED]'                    ['12-digit sequence']
'1234 5678 9012'                                           -> '[REDACTED]'                    ['12-digit sequence']
'1234-5678-9012'                                            -> '[REDACTED]'                    ['12-digit sequence']
'12345678901234'                                            -> unchanged                        []
'my number is 1234 5678 9012 please'                        -> '...please' with [REDACTED]      ['12-digit sequence']
'1234 5678 9012 3456'                                       -> unchanged                        []            (Round 9's B2 case)
'UAN 1000 1234 5678 9012'                                   -> 'UAN 1000 [REDACTED]'            ['12-digit sequence']  (Round 10's B3 case)
'0000-1234 5678 9012'                                       -> '0000-[REDACTED]'                ['12-digit sequence']  (Round 10's B3 case)
'My employee code is 1000 and Aadhaar is 1234 5678 9012'    -> '...is [REDACTED]'               ['12-digit sequence']
```

Both B2 (over-matching into a longer grouped run) and B3 (a real Aadhaar
suppressed by an adjacent unrelated number) are resolved for every case
those two rounds actually constructed. `pytest -q` at HEAD (f6a9556): 52
passed, including a parametrized case for each of these
(`backend/tests/test_scrub.py:9-32`).

### A narrower gap in the same family, found by extending the pattern one step further

The trailing-group heuristic (`backend/scrub.py:43-51`) only fires when
`len(groups) == 4` — i.e., exactly one leading group plus the 4-4-4 Aadhaar
shape. Round 10's fix generalizes "one number right before the Aadhaar" but
not "more than one." Constructed and ran:

```
'UAN 1000 2000 1234 5678 9012' -> 'UAN 1000 2000 1234 5678 9012'  (UNCHANGED)  stripped_types=[]
```

`_GROUPED_DIGIT_RUN` matches all five groups (`1000 2000 1234 5678 9012`,
20 digits total) as one run. `replace_grouped` checks
`digits_only == 12` (false, it's 20) and then `len(groups) == 4` (false,
it's 5) — neither branch fires, so the whole run, including the genuine
trailing Aadhaar-shaped `1234 5678 9012`, is returned untouched. A citizen
mentioning two reference numbers immediately before their Aadhaar (e.g. a
UAN and a separate code, both stated as plain 4-digit groups with no
intervening word) would have that Aadhaar number reach `llm.parse_intake`
unredacted. This is narrower than Round 10's B3 — it requires *two* leading
groups butted up against the real Aadhaar with no separating word, not just
one — but it's the same underlying issue in a form the current fix doesn't
generalize to.

### Blocking
None. The regression from Round 10 (B3) does not reproduce for any input
those two rounds constructed, and the fix is a real improvement over what
came before it.

### Worth fixing
- [W2] `backend/scrub.py:43` the "leading extra group" heuristic only
  handles exactly one leading group (`len(groups) == 4`, i.e. 1 prefix + 3
  Aadhaar groups). A run with two or more leading groups before a genuine
  trailing 4-4-4 Aadhaar (confirmed: `'UAN 1000 2000 1234 5678 9012'`) is
  left completely unredacted. Given the pattern of fixes across Rounds 8-11
  — a boundary case getting patched, then the next boundary case one step
  out failing — this suggests the current approach (match the whole
  variable-length grouped run first, then pattern-match on exactly-4-groups
  in Python) doesn't generalize past the specific shapes tested so far.
  Worth considering scanning for a genuine 4-4-4 Aadhaar-shaped triple
  *anywhere* within a longer grouped run (not just as a fixed suffix of a
  4-group match), rather than special-casing group counts, so the next
  "one more leading group" case doesn't need its own patch.

### Noted, not worth your time today
- [N12] No test in `backend/tests/test_scrub.py` covers a grouped run with
  more than one leading extraneous group (5+ total groups). Worth a case
  here if/when W2 is addressed.

### Verified working
- Ran `pytest -q` at HEAD (f6a9556): 52 passed.
- Re-ran all cases from Rounds 8, 9, and 10 directly against `scrub_text`:
  every previously-reported blocker (B1, B2, B3) is resolved for the exact
  inputs that were used to demonstrate them.
- Constructed one input one step beyond what the current fix generalizes to
  (two leading groups instead of one) and confirmed it reproduces the same
  class of failure as B3, narrower in scope — filed as W2, not blocking,
  since it requires a more specific input shape than any case reported so
  far.

## Round 12, 2026-08-29, reviewing 8b26c17

### Synthetic profiles: fired rules vs. PLAN.md

Ran all five `backend/data/members.json` profiles through the real
`RULES` registry directly (no HTTP, no LLM):

| UAN | Letter | Fired (actual) | PLAN.md expects | Match |
|---|---|---|---|---|
| 999000000001 | A | `[]` | passes everything | yes |
| 999000000002 | B | `['R02', 'R05']` | R05, R02 | yes |
| 999000000003 | C | `['R03', 'R06']` | R03, R06 | yes |
| 999000000004 | D | `['R10', 'R15']` | R10, R15 | yes |
| 999000000005 | E | `['R01', 'R12']` | R12, R01 | yes |

All five match PLAN.md's synthetic-profile table exactly.

### UAN prefix and sensitive-value check

All five keys in `members.json` start with `999`, confirmed by direct
string check. Ran a regex scan of the raw JSON file for any 9+ digit run
and any PAN-shaped token (`[A-Za-z]{5}\d{4}[A-Za-z]`): the only 9+ digit
runs found are the five UAN keys themselves (the intentional synthetic
`999...` values); no PAN-shaped token anywhere in the file. No field value
(names, dates, amounts, member IDs) resembles a real Aadhaar, PAN, or
account number.

### The four endpoints

Confirmed via the app's own OpenAPI schema (`/openapi.json`) that all four
exist as POST routes: `/preflight`, `/override`, `/draft`, `/submit-mock`
(`backend/main.py:82,91,102,108`).

### /override — traced, and confirmed it recomputes rather than caches

`override()` (`backend/main.py:91-99`) does not read or return any cached
verdict. It rebuilds a `MemberProfile` by merging `request.overrides` on top
of `request.state.profile.model_dump()`, validates it, then calls
`_run_preflight(profile, ...)` — which constructs a **fresh**
`PreflightState` and re-invokes `preflight_graph.invoke(...)` from
`intake` all the way through `run_rules`/`order_fixes`/`explain`/`verify`/
`render` again (`backend/main.py:68-79`). Confirmed by running it directly:
started from UAN `999000000002` (fires `R02`, `R05`), overrode
`kyc_approved: True`, and the second response's `fired_results` was
`['R05']` — `R02` genuinely dropped out because the corrected field was
re-run through the real `rule_r02`, not filtered out of a stale result set.

### Priority 1: degraded path through the real HTTP endpoint

Popped `OPENAI_API_KEY` from the real environment (not `monkeypatch`) and
called `POST /preflight` through a `TestClient` with UAN `999000000002`:

- Status `200`, no exception.
- `fired_results` = `['R02', 'R05']` — the verdict is present and correct.
- `rendered_sentences` = the two rules' raw `why` strings
  (`"R02: Your KYC is not approved..."`, `"R05: Your date of exit is
  missing..."`) — the fallback explanation path.
- `explanation.degraded` = `True`.

Matches `backend/AGENTS.md`'s "the app must stay usable with zero model
access" contract, confirmed at the actual API boundary this time, not just
at the `llm.py`/`graph.py` unit level covered in Rounds 5-6.

### Priority 2: raw intake text in the API response

Yes — there is a path where an unscrubbed sensitive string leaves the API.
Called `POST /preflight` with
`intake_text="My Aadhaar is 1234 5678 9012 please check."` and inspected the
full JSON response body:

```
intake_text:    "My Aadhaar is 1234 5678 9012 please check."   <- raw, unscrubbed
scrubbed_text:  "My Aadhaar is [REDACTED] please check."       <- correctly scrubbed
```

`@app.post("/preflight", response_model=PreflightState)`
(`backend/main.py:82`) returns the entire `PreflightState`, and
`PreflightState.intake_text` (`backend/graph.py:24`) is the untouched raw
field — nothing excludes it from serialization. `scrub_text` is only ever
applied on the way *into* `llm.parse_intake` (confirmed correct in Round 8);
it was never meant to, and does not, stop the raw string from being
included in the outgoing HTTP response body. Because `/override` and
`/draft` all take a `state: PreflightState` in their request body and
`/override` returns a fresh `PreflightState` again, the same raw
`intake_text` round-trips through those endpoints too.

To be precise about the actual exposure: this sends the sensitive string
back to the same client that submitted it (the citizen's own browser), not
to a third party — the client already possesses the text it typed. The real
risk is everything *between* server and that response that isn't the
citizen: server access/error logs, any reverse proxy or APM tooling that
logs response bodies, browser extensions, and the fact that the frontend
now holds a `PreflightState` object with the raw string in it for as long
as the page keeps it in memory or `localStorage`, expanding where the raw
value can be captured well past the one deliberate `scrub_text` boundary the
codebase otherwise enforces carefully (Rounds 8-11). Given the amount of
care already spent making sure a scrubbed string reaches the model, and
that `scrubbed_text` already carries everything the UI needs, returning
`intake_text` unscrubbed looks like an oversight rather than a deliberate
choice.

### Blocking
- [B4] `backend/main.py:82` (and by extension `:91`, since `/override`
  round-trips the same field) `PreflightState.intake_text` — the raw,
  unscrubbed citizen input — is included verbatim in the `/preflight` and
  `/override` JSON response bodies. Confirmed with a live request containing
  an Aadhaar-shaped string: the response's `intake_text` field contained it
  unredacted, sitting right next to a correctly-redacted `scrubbed_text`
  field. Fix: exclude `intake_text` from the response (e.g.
  `response_model_exclude={"intake_text"}` on the route, or a separate
  response schema that omits it) since `scrubbed_text` already carries
  everything downstream consumers need.

### Worth fixing
None beyond B4.

### Noted, not worth your time today
- [N13] `backend/tests/test_main.py` covers `/preflight`, `/override`
  (recompute), and `/submit-mock`, all with `TestClient`, but none of its
  three tests inspect `intake_text` in the response body, and none use
  intake text containing a sensitive pattern — so B4 exists at HEAD despite
  the suite being green. Once B4 is fixed, a test asserting `intake_text`
  is absent (or scrubbed) from the `/preflight` response would prevent it
  from coming back. Also worth a case for the `OPENAI_API_KEY`-unset path
  through the real endpoint (this round's Priority 1 check) and a
  `/draft` test, since neither is covered yet either.

### Verified working
- Ran `pytest -q` at HEAD (8b26c17): 55 passed. Correction: I initially
  (incorrectly) reported no `test_main.py` existed at this commit before
  checking — it does, and it's green; it just doesn't cover the raw-text
  leak in B4 (see N13).
- Ran all five synthetic profiles through the real `RULES` registry: fired
  sets match PLAN.md exactly for all five.
- Confirmed all UANs start with `999` and scanned the raw JSON for any
  Aadhaar/PAN-shaped value beyond the UAN keys themselves: none found.
- Confirmed all four endpoints exist via the app's own OpenAPI schema.
- Traced and ran `/override`: confirmed it recomputes through the full
  graph rather than serving a cached result, by overriding a field and
  observing the previously-fired rule actually drop out.
- Ran `/preflight` with `OPENAI_API_KEY` popped from the real environment:
  200, verdict present, fallback explanations, `degraded=True`, no
  exception.
- Ran `/preflight` with a live Aadhaar-shaped string in `intake_text` and
  confirmed it comes back unredacted in the response body — see B4.

## Round 13, 2026-08-29, reviewing 6582f76 — review of the B4 fix

### The change

`backend/main.py` no longer returns `PreflightState` (the full LangGraph
state, including raw `intake_text`) from `/preflight` or `/override`.
Instead both routes now return a new `PreflightResponse` model
(`backend/main.py:31-43`) that only carries `profile`, `language`,
`scrubbed_text`, `stripped_types`, a derived `verdict`, `ordered_issues`,
`verified_sentences`, and `needs_human_review` — `intake_text` is not a
field on it at all, so there's nothing to exclude at serialization time; it
structurally cannot appear. `OverrideRequest`/`DraftRequest`/
`SubmitMockRequest` now take this sanitized `PreflightResponse` as their
`state`, not the raw `PreflightState`, so raw text can't re-enter through
those either. `/override`'s recompute now seeds the graph with
`request.state.scrubbed_text` (`backend/main.py:132`) instead of a raw
`intake_text` it no longer has access to — the already-redacted text is
scrubbed again (a no-op, since `[REDACTED]` matches no sensitive pattern)
and that's what reaches `llm.parse_intake` on override, same as first pass.

### B4 — re-verified live, both endpoints

Ran the same live request as Round 12, with an Aadhaar-shaped string, then
fed the response into `/override`:

```
POST /preflight {uan: 999000000002, intake_text: "My Aadhaar is 1234 5678 9012 please check."}
-> status 200
-> "intake_text" in response body: False
-> raw digits ("1234 5678 9012" / "123456789012") anywhere in response text: False
-> scrubbed_text: "My Aadhaar is [REDACTED] please check."

POST /override {state: <above response>, overrides: {}}
-> status 200
-> "intake_text" in response body: False
-> raw digits anywhere in response text: False
```

Checked the full raw response *text*, not just the parsed JSON's top-level
keys, so this also rules out the raw string surviving inside some other
field (e.g. embedded in an error message or a nested object) rather than
literally under an `intake_text` key. B4 is resolved for both endpoints.

### Everything else from Round 12, re-run against this HEAD

- **Synthetic profiles vs. PLAN.md**: re-ran all five directly against
  `RULES` — unchanged from Round 12, all five still match
  (A: `[]`, B: `['R02','R05']`, C: `['R03','R06']`, D: `['R10','R15']`,
  E: `['R01','R12']`). This commit didn't touch `rules.py` or the fixture
  data, so no regression expected or found.
- **Four endpoints**: still all present per `/openapi.json`
  (`/preflight`, `/override`, `/draft`, `/submit-mock`).
- **/override still recomputes, not caches**: re-ran the same trace —
  UAN `999000000002` (`R02`, `R05`) with `kyc_approved` overridden to
  `True` now returns `ordered_issues == ['R05']`, i.e. `R02` genuinely
  dropped from a fresh rule run, not a filtered stale list. `verdict` also
  recomputes correctly (`"REJECTED"` while any `BLOCKER` remains in
  `ordered_issues`).
- **Priority 1, degraded path, re-run live**: `OPENAI_API_KEY` popped from
  the real environment, `POST /preflight` on UAN `999000000002` still
  returns `200`, `verdict: "REJECTED"`, `ordered_issues: ['R02', 'R05']`,
  and `verified_sentences` carrying the two rules' raw `why` strings — the
  fallback path still works end to end through the new response shape.

### Tests

`backend/tests/test_main.py:57-81` adds
`test_preflight_and_override_never_return_raw_intake_text`, which checks
both the sensitive substring (`"1234 5678 9012"`, `"123456789012"`) and the
literal key `"intake_text"` are absent from both `/preflight` and
`/override` response bodies — the same two things I checked by hand above,
now as a permanent regression test. `pytest -q` at HEAD (6582f76): 56
passed.

### Blocking
None. B4 is resolved and covered by a real regression test that checks the
response body text, not just key presence.

### Worth fixing
None.

### Noted, not worth your time today
- [N14] Still open from Rounds 10/11: `voi.py`'s cache-key-adjacent items
  aside, the scrub boundary itself (W2 from Round 11 — a grouped run with
  two or more leading extraneous groups before a genuine Aadhaar) is
  untouched by this commit. Not this round's scope, just flagging it's
  still on the books.
- [N15] The `/draft` and `/submit-mock` HTTP endpoints are still not
  exercised by `test_main.py` beyond the one `/submit-mock` happy-path test
  added earlier; `/draft` has no HTTP-level test at all (same gap noted as
  N13 in Round 12, not yet addressed — reasonable, since it wasn't this
  commit's job).

### Verified working
- Ran `pytest -q` at HEAD (6582f76): 56 passed.
- Re-verified B4 live against both `/preflight` and `/override` with a
  fresh Aadhaar-shaped request, checking the full response text (not just
  top-level keys) for both the literal `intake_text` key and the raw
  sensitive substring: absent in both endpoints' responses.
- Re-ran all five synthetic profiles, the four-endpoint check, the
  `/override` recompute trace, and the degraded-path check from Round 12
  against this HEAD: all still hold, no regressions from the response-model
  change.

## Round 14, 2026-08-29, reviewing 2f6c3d1

### The fix

`resolve_profile` (`backend/graph.py:79-97`) now only applies an
intake-derived `claim_type`/`claim_purpose` when the field name is in a new
`state.unknown_fields` list **and** the loaded profile's value is falsy
**and** the model returned a non-`None` value. `date_of_exit` and
`kyc_approved` were never touched by `resolve_profile` at any point — they
aren't fields on `IntakeResult` at all (`backend/llm.py:16-24`), and
`IntakeResult`'s `extra="forbid"` means the model can't smuggle them in
under a different key either. So for those two fields, "the model cannot
change a loaded field" was already structurally true before this commit,
independent of the new gate.

### Requested scenario: run with a stub trying to rewrite all four fields

Ran UAN `999000000002` (loaded `claim_type="FINAL_SETTLEMENT"`,
`date_of_exit=None`, `kyc_approved=False`) through the real compiled graph
with a stub `llm.parse_intake` returning
`claim_type="PENSION_WITHDRAWAL"`, `claim_purpose="MEDICAL"` (the two
fields `IntakeResult` can express):

```
final profile claim_type:    'FINAL_SETTLEMENT'   (unchanged)
final profile claim_purpose: 'FINAL_SETTLEMENT'   (unchanged)
final profile date_of_exit:  None                 (unchanged)
final profile kyc_approved:  False                (unchanged)
fired_results: ['R02', 'R05']
```

All four fields are unchanged and both `R02` and `R05` still fire, matching
what was asked. The fix is structural for `claim_type`/`claim_purpose`
(gated in `resolve_profile`) and structural-by-schema for
`date_of_exit`/`kyc_approved` (never representable in `IntakeResult` to
begin with). This matches
`test_loaded_profile_fields_cannot_be_overwritten_by_intake`
(`backend/tests/test_graph.py:87-104`), added in this commit.

### The "empty check" question: does a present-but-empty field still block correctly?

Yes, and for a reason worth being precise about: `not state.profile.claim_type`
is `True` whenever the loaded value is falsy — `""`, `None` (not applicable,
field is typed `str`), etc. The bug this commit fixed was never about that
check failing to treat "empty" correctly; the previous code
(`if state.intake_result.claim_type is not None: profile_updates[...] = ...`)
had **no profile-side check at all** — it applied the model's value
whenever the model returned *anything* non-`None`, regardless of whether
the loaded profile already had a real value. So "does the empty check let
something slip through" doesn't quite apply to the old bug's mechanism; the
old bug was an unconditional overwrite, not a leaky emptiness check. The new
`not state.profile.claim_type` check itself is correct: it can't be
tricked by a present non-empty value, since any truthy string makes it
`False` and blocks the update. Confirmed via the scenario above (loaded
`"FINAL_SETTLEMENT"` stayed put against a rewriting stub).

### The reverse check: does legitimate intake still work for a genuinely unknown field?

No — this is broken. `state.unknown_fields` (`backend/graph.py:29`) is
declared on `PreflightState` but **nothing in the codebase ever populates
it**. Confirmed by grepping the whole repo for `unknown_fields`: it appears
only as the field declaration, its two `in` checks in `resolve_profile`,
and unrelated uses of the same name as a parameter in `voi.py`'s
`questions_worth_asking` — no node, no route in `backend/main.py`, and no
test ever assigns a value to `PreflightState.unknown_fields`. It is always
`[]` by default, for every real code path, so
`"claim_type" in state.unknown_fields` is always `False` and
`resolve_profile`'s intake-derived update can never fire — not just for
protecting an already-loaded value, but for a genuinely blank one too.

Ran it directly: a `MemberProfile(claim_type="")` (truly unknown) through
the real graph with a stub `parse_intake` returning
`claim_type="PENSION_WITHDRAWAL"` and no `unknown_fields` set on the initial
state (which is exactly how `backend/main.py`'s `_run_preflight`
constructs its initial `PreflightState` — it never sets `unknown_fields`
either):

```
unknown_fields on initial state (default): []
final profile claim_type (should be filled if intake path works): ''
```

The field stays blank. Free-text intake can no longer populate `claim_type`
or `claim_purpose` for any profile, ever, through the current wiring — the
gate meant to distinguish "fill this in" from "don't touch this" always
resolves to "don't touch this," because nothing computes and sets the
`unknown_fields` list the gate depends on. This is a real regression in
legitimate intake behavior, introduced by this fix, not merely a
theoretical gap: prior to this commit, `resolve_profile` did apply
intake-derived values (that was the whole bug — it applied them
unconditionally); after this commit, it never applies them at all, correct
loaded-field case or not.

### Blocking
- [B5] `backend/graph.py:29,85,91` `state.unknown_fields` is never assigned
  anywhere in the codebase (checked `graph.py`, `main.py`, every test) —
  always `[]`. Because `resolve_profile`'s intake-fill branches both require
  `field in state.unknown_fields`, this makes `resolve_profile` a
  structural no-op for every profile, including ones where `claim_type`/
  `claim_purpose` are genuinely blank and should be filled from the
  citizen's free text. Confirmed live: a profile with `claim_type=""` stays
  `""` after a full graph run even when the stubbed model correctly returns
  a value for it. This over-corrects the original bug — the fix needed
  something that actually computes which fields are unknown (e.g. checking
  blank/`None` fields on `state.profile`, which is exactly what
  `not state.profile.claim_type` already does one line later) and populates
  `unknown_fields` before or within `resolve_profile`, or drops the
  `unknown_fields` gate entirely and relies on the `not state.profile.X`
  check alone, which is sufficient by itself to prevent the original
  overwrite bug (as demonstrated in the "empty check" section above — it
  already correctly blocks on any truthy loaded value with no help from
  `unknown_fields`).

### Worth fixing
None beyond B5.

### Noted, not worth your time today
- [N16] `test_loaded_profile_fields_cannot_be_overwritten_by_intake`
  (`backend/tests/test_graph.py:87-104`) only exercises the
  already-populated-field case (`_MEMBERS["999000000002"]`, which has a
  real `claim_type`). No test in the suite constructs a profile with a
  blank `claim_type`/`claim_purpose` and checks intake still fills it in —
  that's exactly the gap that let B5 land with 57/57 tests green.

### Verified working
- Ran `pytest -q` at HEAD (2f6c3d1): 57 passed.
- Ran the requested scenario (UAN `999000000002`, stub rewriting
  `claim_type`/`claim_purpose`, `date_of_exit`/`kyc_approved` not
  representable in `IntakeResult`) through the real compiled graph: all
  four fields unchanged, `R02` and `R05` both still fire — matches what was
  asked, output shown above.
- Grepped the full repository for `unknown_fields`: confirmed it is never
  assigned anywhere outside its own declaration and the two gate checks.
- Ran the reverse case directly: a profile with a genuinely blank
  `claim_type`, full graph run, stub model returning a valid value — the
  field stayed blank. This is B5.

## Round 15, 2026-08-29 — author context on B5, reassessed severity

The author states this is deliberate: all five demo profiles supply every
field the rules read, so intake-fill is inert by design in this prototype,
and a model should never be able to change a field that decides
eligibility.

Checked `backend/data/members.json` directly: confirmed all five profiles
have non-empty `claim_type` and `claim_purpose` (`FINAL_SETTLEMENT`/
`PARTIAL_WITHDRAWAL` and `FINAL_SETTLEMENT`/`MEDICAL` respectively, across
all five). So the author is right about the practical consequence today:
`not state.profile.claim_type` already evaluates `False` for every one of
the five shipped profiles independent of `unknown_fields`, so B5 causes no
observable behavior difference in this demo right now — no citizen
interaction, real or synthetic, currently exercises the intake-fill branch.
Downgrading from Blocking.

That said, two things from Round 14 stand regardless of demo scope, so I'm
not fully retracting the finding, just its severity:

1. "The loaded record is a source of truth a model cannot change" is a
   property of the `not state.profile.claim_type` check alone — that part
   is real and correctly enforced (verified in Round 14). `unknown_fields`
   contributes nothing to that guarantee; it's a second, independent gate
   that happens to only ever narrow what still passes it, never widen it.
2. Whether the intake-fill path is meant to be reachable in this build is a
   separate question from whether it's *wired correctly* for whenever it
   is exercised. `resolve_profile`'s docstring
   (`backend/graph.py:80`, "Fill explicitly unknown, empty fields without
   replacing profile truth") states it fills unknown fields; the code
   cannot do that today because nothing populates `unknown_fields`. If a
   sixth profile ships with a blank `claim_type`, or the clarify loop's
   answer is ever meant to feed back into `unknown_fields`/the profile,
   this stays silently broken with no test to catch it — same conclusion
   as Round 14, just scoped to "not urgent for today's five profiles"
   rather than "broken right now."

### Blocking
None (B5 downgraded — see above).

### Worth fixing
- [W3] (downgraded from B5) `backend/graph.py:29,85,91`
  `state.unknown_fields` has no producer anywhere in the codebase, so
  `resolve_profile`'s intake-fill branches can never fire. Causes no
  observable defect against the five current demo profiles, all of which
  have `claim_type`/`claim_purpose` already populated. Two options, either
  is fine for a hackathon build: (a) wire something to populate
  `unknown_fields` (e.g. blank-check `state.profile` before intake, mirror
  what `not state.profile.claim_type` already does) if a future profile or
  the clarify loop is meant to exercise this path, or (b) if intake-fill is
  genuinely out of scope for this build, drop the `unknown_fields` field and
  gate, and let `not state.profile.claim_type` be the single, sufficient
  guard — simpler, and the docstring stops promising behavior the code
  doesn't have.

### Noted, not worth your time today
- [N17] If (b) above is chosen, `resolve_profile`'s docstring should also
  change — it currently says "fill explicitly unknown, empty fields," which
  won't be true once `unknown_fields` is removed and the function starts
  meaning "load-time value wins, always."

### Verified working
- Confirmed via `backend/data/members.json` that all five demo profiles
  have `claim_type` and `claim_purpose` already populated, so B5/W3 has no
  effect on any currently shipped profile or citizen-facing path.
