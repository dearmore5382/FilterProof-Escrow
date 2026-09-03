# Escrow semantic preview — four frozen cases passed

User-deployed escrow: `0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29`.
Deployed source matches SHA-256
`326e46f225bc2e88e0cefb581a8b5cbf450f3322017993098794bdcf5d3ff2a9`.

Machine-readable evidence:
`escrow-preview-0xf99765498d9f2df004ce5b117b78fb5ebb68cd29-results.json`.
Includes exact arguments, UTC start times, returned observations/outcomes and
counts readbacks; sensitive node configuration is not exported.

| Frozen case | Actual result | Expected check |
| --- | --- | --- |
| positive | SUCCESS; SERVICE_CONFIRMED / ALL_CHECKS_CONFIRMED | PASS |
| wrong-manifest-hash | SUCCESS; MATERIAL_FAILURE / MANIFEST_BINDING_MISMATCH | PASS (expected business rejection) |
| cross-job | SUCCESS; MATERIAL_FAILURE / MANIFEST_BINDING_MISMATCH | PASS (expected business rejection) |
| invalid-url | ERROR; INVALID_MANIFEST_URL | PASS (expected execution rejection) |

Positive observations: binding_status MATCH, asset_identity MATCH,
filter_replacement COMPLETE, before_after_continuity CONSISTENT,
pressure_evidence PLAUSIBLE, tamper_signal NONE. The same deployed helpers,
prompts, parser and derivation are used by actual assessment. All source
checks succeeded; counts were `0|0` before and after every case. Every case
ran once; no source/input substitution, automatic retry or changed expectation.

The input is the original publicly disclosed synthetic maintenance fixture.
This is not a real service record or water-safety certification.

## Scope and next gate

All four were **unsigned remote leader snapshot simulations**, not finalized
transactions or multi-validator consensus. No jobs/attempts were created and
the assistant sent no funding, signing or settlement transaction. Preview
SERVICE_CONFIRMED does not set RELEASE_AUTHORIZED or pay anyone.

This closes the frozen semantic preview matrix, not the full adversarial audit.
Next is an explicitly authorized small testnet funded lifecycle on this same
source/address: create → fund → submit → assess → release, checking finalized
execution, consensus, exact readback and child transfer/balance effects. The
remaining failures and multi-transaction combinations in LIVE_MATRIX.md follow.
Keep the frontend disabled until the live gates pass. No redeployment is needed
for the next test on the currently unchanged source.
