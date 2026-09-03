# Deployment readiness — READY FOR USER REDEPLOYMENT

The user performs deployment. The first deployment was safely tested and refunded, but its three-image vision call is incompatible with the active validator limit. A corrected source must be deployed at a new address.

## Passed locally

- Contract: 37 pytest tests, including 729 closed-observation combinations inside one exhaustive test; independent captured-validator tests; state/authority/replay/custody regressions; synthetic-fixture integrity checks.
- GenVM syntax/semantic validation and SDK typecheck.
- Frontend: ten unit tests, application-source lint and full TypeScript check; production build passes.
- English UI, original supplied logo, no private keys and no fallback contract address.
- Persistent hash journal, source-parity guard and interrupted-submission intent implemented.
- Dependency audit reported zero known vulnerabilities after version updates and SDK installation. This is not a security guarantee.

## Pre-deployment evidence resolved

1. A coherent synthetic positive candidate exists under `fixtures/synthetic-happy`; it is visibly labeled and is not a real maintenance record.
2. All three exact PNG bytes are pinned with CIDv1. The compact WebP correction set is commit-pinned on GitHub. Public downloads returned HTTP 200 and matched local byte counts and SHA-256 hashes.
3. The two-image validator limit found by the first live audit is fixed. All three files remain independently fetched and hash-verified; only BEFORE and AFTER are passed to the vision model.
4. Contract source hash was recomputed after all local gates.

## Post-deployment gates

1. Deploy the corrected source at a new address and verify initial counts `0|0` plus source parity.
2. Run the predefined live matrix, including GenLayer acquisition/model behavior, consensus and emitted payout/refund transfer execution.
3. Run browser-wallet end-to-end tests, including multi-tab/refresh/error recovery. Unit tests do not replace these.
4. Exercise the optional WebMCP readback tool in a supported WebMCP browser context if that optional feature is claimed.

The corrected source passed the full local gate and is ready for user redeployment. The old address must not be configured in the frontend. This is not an audit-complete or production-ready claim.

Candidate source SHA-256: `d9c9843009c1ee9810302957bcaf9650c305e0ccf7dbf3f5283c7abaffad5bc6`.
