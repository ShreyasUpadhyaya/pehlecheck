# PehleCheck: build plan

## The problem

Over a quarter of EPF claims are rejected. Final settlement rejections rose
from 13% to 34% across five years (Indian Express, Feb 2024, on EPFO records).
Almost none are eligibility failures. They are name mismatches, a missing exit
date, a stale IFSC. The citizen learns weeks later in a one-line internal
remark they cannot decode, then refiles blind.

## The product

Show the rejection before it happens. Citizen describes the situation in plain
Hindi or English, the system runs their record against 15 encoded rejection
rules, and returns a verdict with the exact field that failed, who has to fix
it, how long it takes, and in what order.

## Citizen journey (all seven steps must work end to end)

1. Land, pick language, enter a demo UAN printed on the page.
2. Describe the situation in free text.
3. Answer at most two clarifying questions, asked only if the answer can flip
   a rule.
4. Verdict screen: "This claim will be rejected today. 2 blockers, 1 warning."
5. Issue cards: explanation, then field and observed value, then actor and eta.
6. Override anything wrong, recompute. Generate the employer or grievance
   draft. Tick the review box, which enables submit.
7. Fix the seeded defects, re-run, clean pass, mock submit, outcome screen.

## In scope

Rules engine, dependency ordering, plain-language explanation with a citation
gate, value-of-information clarification, sensitive-data scrubbing, override
and recompute, draft generation, Hindi and English, mock submission, a
limitations page, green hermetic tests.

## Out of scope

Live government APIs. Real Aadhaar, PAN, OTP, payments, or citizen records.
Automated submission anywhere. Admin panels. Multi-service coverage.
Vector search. Any auth beyond a demo UAN selector.

## The 15 rules

Format for Codex prompts: id, field read, fire condition, severity, actor, eta.

| id | field read | fires when | severity | actor | eta |
|---|---|---|---|---|---|
| R01 | `uan_activated` | is false | BLOCKER | CITIZEN | 1 |
| R02 | `kyc_approved` | is false | BLOCKER | EMPLOYER | 7 |
| R03 | `name_as_per_epfo`, `name_as_per_aadhaar` | normalized forms differ | BLOCKER | CITIZEN | 15 |
| R04 | `dob_epfo`, `dob_aadhaar` | differ | BLOCKER | CITIZEN | 15 |
| R05 | `date_of_exit` | is null and `claim_type` is FINAL_SETTLEMENT | BLOCKER | EMPLOYER | 10 |
| R06 | `bank_ifsc_verified` | is false | BLOCKER | BANK | 3 |
| R07 | `account_holder_name`, `name_as_per_epfo` | differ, or account is joint | BLOCKER | CITIZEN | 5 |
| R08 | `aadhaar_seeded` | is false | BLOCKER | CITIZEN | 3 |
| R09 | `service_months` | under 6 and `claim_type` is PENSION_WITHDRAWAL | BLOCKER | CITIZEN | 0 |
| R10 | `service_months` | under 60 and `claim_amount` above the tax threshold | WARNING | CITIZEN | 1 |
| R11 | `employment_status`, `claim_type` | still EMPLOYED and claim is FINAL_SETTLEMENT | BLOCKER | CITIZEN | 60 |
| R12 | `member_ids` | more than one and any untransferred | BLOCKER | CITIZEN | 20 |
| R13 | `eps_contribution_months`, `service_months` | EPS months short of service months | WARNING | EMPLOYER | 15 |
| R14 | `claim_amount`, `claim_purpose` | amount exceeds the purpose limit | BLOCKER | CITIZEN | 0 |
| R15 | `claim_type`, `claim_purpose` | form does not match the stated purpose | BLOCKER | CITIZEN | 0 |

Every `RuleResult` carries a `source_note`: which public guidance it was
encoded from, plus "reviewed 29 Aug 2026, not authoritative".

## Dependency edges for `deps.py`

Fix order is a topological sort over these, blockers before warnings, and
within a tier, whichever unblocks the most other rules first.

- R02 depends on R08 (KYC cannot be approved before Aadhaar is seeded)
- R06 depends on R02
- R07 depends on R02
- R05 depends on R11 (exit date is meaningless while still employed)
- R12 depends on R01
- R13 depends on R05

## Synthetic profiles in `data/members.json`

UANs start with 999 so nobody mistakes them for real. Names obviously fictional.

- A: clean, passes everything. The happy path for the video's final beat.
- B: R05 and R02 fire. The main demo profile.
- C: R03 and R06 fire.
- D: R10 and R15 fire.
- E: R12 and R01 fire.

## Degradation

If `OPENAI_API_KEY` is absent or the call fails, the explainer returns
`RuleResult.why` verbatim and the UI shows a small note that plain-language
mode is unavailable. The verdict, ordering, override, and submit flow all still
work. This is deliberate and gets said out loud in the video.

## Schedule, 29 Aug

| Window | Codex | While it cools |
|---|---|---|
| 1 | models, rules, tests | write members.json by hand, sketch UI |
| 2 | graph, deps, verify | VerdictHeader and layout |
| 3 | voi, scrub, main.py | wire frontend to API |
| 4 | UI skeleton, bug fixes | limitations page, i18n, deploy |
| 5 | reserve | video, summary, submit |

Submit a working version by early evening. Resubmit later if improved. Latest
response wins. Form closes 10:00 PM IST with no grace period.

## Cut order under pressure

Voice input, then Hindi explanations (keep the toggle), then the drafter,
then the dependency DAG (flat blockers-then-warnings sort).

Never cut: rules engine, fix-and-resubmit loop, limitations page, green tests.
