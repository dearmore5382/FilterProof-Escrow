# Deployment readiness — FUNDED HAPPY PATH PASSED; ADVERSARIAL MATRIX OPEN

**One funded synthetic happy path passed end to end.** On escrow
`0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29`, all five parent writes finalized
with MAJORITY_AGREE, assessment authorized release, accounting reached PAID,
and exactly one finalized child transfer increased the technician balance by
0.1 GEN. Contract balance is zero. See `FUNDED_HAPPY_PATH.md` and its public
JSON ledger. Four post-terminal unsigned leader simulations also passed with
state unchanged: assessment replay, duplicate release, refund after payment
and late proof. They are not signed transactions or consensus evidence. This
does not close remaining failure/adversarial/frontend gates.

**Low-value failure smoke passed within its declared boundary.** A 0.01 GEN
draft was never funded: create and cancel finalized with majority agreement,
while eight authority/value/state-machine failures passed as unsigned leader
simulations with unchanged state and balances. See `FAILURE_SMOKE_RESULTS.md`.
F1–F3 remain partial because those negative calls were not consensus writes.

**F6 passed for the frozen binding-mismatch scenario.** A separately bounded
0.01 GEN lifecycle preserved two append-only failed attempts, authorized refund
on the second assessment and returned the exact amount through one finalized
child transfer. All seven parent writes finalized with majority agreement; the
contract balance ended at zero. See `REFUND_PATH_RESULTS.md`.

**F7 passed for a funded job with no proof.** Early recovery returned
RECOVERY_TOO_EARLY in a state-preserving unsigned simulation. After deadline,
the technician wallet invoked permissionless recovery; the parent and exact
0.01 GEN refund child finalized and contract balance returned to zero. See
`EXPIRY_RECOVERY_RESULTS.md`.

**F4 partially passed in unsigned preview.** Pinned 404 and oversized sources
failed closed as EVIDENCE_UNAVAILABLE without state mutation. Empty/429/5xx and
multi-validator negative execution remain open. See `SOURCE_FAILURE_PREVIEW_RESULTS.md`.

**User deployed; all four semantic preview cases passed.** Address:
`0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29`. Source parity and counts `0|0`
verified before/after each case. Positive returned SERVICE_CONFIRMED with exact
all-positive observations; three negative cases matched frozen expectations.
See `ESCROW_PREVIEW_RESULTS.md`. No signed transactions/funding occurred.
The next gate is authorized testnet funded lifecycle/consensus, not redeployment.
Current full local suite: 201 passed; lint/validation/typecheck pass.

Latest diagnostic: v3 at `0x9Bed86f3ccf45b778c09e33A91aD14e5C65c3857`.
Source-verified remote control and both two-PNG JSON cases passed once each;
visible lengths 127 and 37. See `PNG_PROBE_V3_FINDINGS.md`. These are unsigned
leader simulations, not consensus or escrow happy-path evidence. Prior local
suite at v3 handoff: 177 passed plus lint/validation/typecheck. Escrow funding
and release remain blocked by semantic/live gates; no further image probe needed.

Reusable diagnostic v2 was deployed by the user at
`0x767a4a1b0549f298c12A74f4CF5ce810d729cA83`. Source-verified remote simulations:
control, three-file PNG fetch/hash and one-PNG JSON round trip pass. Two-PNG
model call returns a dict but fails the diagnostic `PROBE_OUTPUT_VISIBLE`
guard. Testing stopped there; see `PNG_PROBE_FINDINGS.md`. Current combined
local suite at v2 handoff: 120 passing tests. No escrow happy path or consensus is proved.

The user performs deployment. Earlier simulations identify WebP rejection (`INVALID_IMAGE`). PNG transport passed on v3 and actual escrow semantic preview now passes. Funded happy path and multi-validator consensus remain unverified. See `ESCROW_PREVIEW_RESULTS.md` for current evidence and `VISION_DIAGNOSIS.md` for history.

## Passed locally

- Combined current suite: 201 pytest tests, including 729 closed-observation combinations and 36 pair-merge combinations; exact SDK payload capture, independent captured-validator tests, preview safety, funded-lifecycle, post-terminal, failure-smoke, refund-path, expiry-recovery and source-failure runner guards, unsupported-byte correction, state/authority/replay/custody regressions and fixture integrity checks.
- GenVM syntax/semantic validation and SDK typecheck.
- Frontend: 11 unit tests, application-source lint, full TypeScript check and production build passed after the format guard change. Sites publishing is deferred until the live audit gate passes.
- English UI, original supplied logo, no private keys and no fallback contract address.
- Persistent hash journal, source-parity guard and interrupted-submission intent implemented.
- Dependency audit reported zero known vulnerabilities after version updates and SDK installation. This is not a security guarantee.

## Pre-deployment evidence resolved

1. A coherent synthetic positive candidate exists under `fixtures/synthetic-happy`; it is visibly labeled and is not a real maintenance record.
2. All three original PNG bytes are pinned with CIDv1 and also exist at GitHub commit `56ca76cb35b4835f2d64b30cdce49aecc80c2942`. The original public manifest.json (Pinata image URLs) and all PNG hashes were rechecked successfully; the unpublished alternate manifest-png.json is not required for this preview. Historical WebP files must not be used for happy-path attempts.
3. All three files are independently fetched and hash-verified, then inspected in two calls of two images each. Negative/uncertain detail cannot be overridden by positive overview observations.
4. Local contract gates pass, but they mock the model boundary and therefore cannot prove live vision compatibility.

## Post-deployment gates

1. Completed: source-verified deployed probe simulations isolate INVALID_IMAGE for WebP; no-image text and JSON round trips work. This is leader simulation evidence, not network consensus.
2. Completed: user deployment, exact source and four-case semantic preview on the escrow, using the original public PNG manifest.
3. Completed: authorized 0.1 GEN synthetic happy lifecycle, consensus/readback and child transfer verification.
4. Completed: four zero-value post-terminal snapshot simulations on the paid job; all returned the expected rejection and state remained unchanged. This does not replace consensus testing.
5. Completed: F6 binding-mismatch correction/refund lifecycle with exact child transfer and balance verification.
6. Next: run remaining failure, recovery and adversarial combinations without reusing completed jobs or exceeding bounded test amounts.
7. Run browser-wallet end-to-end tests, including multi-tab/refresh/error recovery. Unit tests do not replace these.

Neither superseded escrow address nor the diagnostic probe may be configured in the frontend. The WebP cause is identified, but this is not a release-ready source until PNG vision and the live matrix pass.

Candidate source SHA-256: `326e46f225bc2e88e0cefb581a8b5cbf450f3322017993098794bdcf5d3ff2a9`.
