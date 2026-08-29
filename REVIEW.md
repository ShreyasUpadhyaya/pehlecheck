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
