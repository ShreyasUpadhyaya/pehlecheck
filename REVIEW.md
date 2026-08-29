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
