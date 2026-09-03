# Escrow candidate — user deployment for zero-funds preview

Completed: user deployed `0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29`.
Exact-source preflight and all four frozen unsigned preview cases passed once.
See `ESCROW_PREVIEW_RESULTS.md`. The steps below are retained as the frozen
historical plan, not instructions to deploy again or repeat completed cases.

Deploy **contracts/FilterProofEscrow.py**, not another image probe.
Constructor: no arguments. Attached Value: **0**. Do not call fund_job yet.

Source SHA-256:
`326e46f225bc2e88e0cefb581a8b5cbf450f3322017993098794bdcf5d3ff2a9`.
Schema: 13 public methods (4 views, 9 writes), including `preview_proof`.

## Why this source change

The original PNG transport matrix passed on v3. Its diagnostic descriptions
do not execute the escrow's closed-field classifier. That probe cannot accept
arbitrary assessment prompts. A no-model constructor snapshot with explicit
UTC produced a real storage `forbidden` error before constructor execution;
see `CONSTRUCTOR_SNAPSHOT_FINDINGS.md`. No on-chain code changed.

The candidate adds a zero-value, non-persisting preview entry point to the
escrow itself. It reuses the **same** `_consensus_observation`, image fetch/hash,
vision prompts, parsers, `_merge_views` and `_derive_outcome` as assessment.
No existing classifier, payout criteria or funded lifecycle has been relaxed.
A preview result is explicitly labeled `PREVIEW_ONLY_NO_PAYMENT_AUTHORIZATION`.

This avoids another standalone semantic probe deployment. If semantic and
subsequent live gates pass without a source fix, the same escrow address can
be used for the funded workflow. This is not a promise that future tests pass.

## Local gates

- Full Python suite: **194 passed**, including 12 preview behavioral tests,
  no-storage static check, 3 preview-runner checks and one snapshot parameter test.
- GenVM lint, validation/schema and SDK typecheck pass.
- Preview guards reject value/invalid inputs before nondeterminism; positive
  preview cannot create jobs/attempts or unlock a funded job; runtime failures
  preserve state; independently negative validator rejects positive leader.
- Existing lifecycle/failure/adversarial tests retained. Direct Mode uses
  mocked web/model; no live semantic or consensus success is claimed.
- Frontend unchanged and disabled. Prior frontend checks are historical;
  browser-wallet audit remains required. No secret or signing key is needed
  for this preview sequence.

## Exact public fixture

Use the original `fixtures/synthetic-happy/manifest.json`, already public at
[full GitHub commit](https://raw.githubusercontent.com/dearmore5382/FilterProof-Escrow/56ca76cb35b4835f2d64b30cdce49aecc80c2942/fixtures/synthetic-happy/manifest.json).
Manifest SHA-256:
`35aad96156bd14fa6e3797ee88a8e71461d208caa8472c633027b5db4b9cd992`.

It references the original three PNGs on Pinata, with the **same image hashes**
tested on GitHub by v3. This is a disclosed host-path distinction, not an image
substitution. Manifest and all three images returned HTTP 200 with exact hashes
on 2026-09-03; see `preview-fixture-preflight.json`. That check is developer HTTP
only. The deployed preview must independently re-fetch/hash through GenLayer.
No new files were uploaded. The alternate all-GitHub `manifest-png.json` remains
unpublished and is not used by this frozen preview sequence.

## Frozen remote matrix (one invocation per case, stop on unexpected outcome)

All calls below are unsigned leader `sim_call` snapshots. No deployment,
signed transaction, custody changes or multi-validator consensus is implied.
The runner verifies exact source and fresh counts `0|0` before/after each
simulation, saves sanitized receipts and prevents automatic duplicate attempts.

```powershell
python -m diagnostics.run_escrow_preview preflight --contract <ESCROW_ADDRESS>
python -m diagnostics.run_escrow_preview positive --contract <ESCROW_ADDRESS>
python -m diagnostics.run_escrow_preview wrong-manifest-hash --contract <ESCROW_ADDRESS>
python -m diagnostics.run_escrow_preview cross-job --contract <ESCROW_ADDRESS>
python -m diagnostics.run_escrow_preview invalid-url --contract <ESCROW_ADDRESS>
```

| Case | Expected result |
| --- | --- |
| positive | SERVICE_CONFIRMED / ALL_CHECKS_CONFIRMED, exact all-positive closed observations |
| wrong-manifest-hash | MATERIAL_FAILURE / MANIFEST_BINDING_MISMATCH; no vision |
| cross-job | Same committed job-0 manifest evaluated as job 1: binding mismatch; no vision |
| invalid-url | Execution rejection INVALID_MANIFEST_URL before fetch/model |

All leave counts `0|0`; none authorizes payout. A positive mismatch stops the
sequence for diagnosis, not another attempt or a looser expected verdict.
This small matrix does not replace the full live adversarial audit.

After preview passes, use `LIVE_MATRIX.md` to verify actual funded lifecycle,
FINALIZED execution/consensus/readback, child transfers and replay safety.
Funding and frontend release are separate gates. The assistant does not deploy.
