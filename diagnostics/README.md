# FilterProof Vision Probe — manual deployment handoff

Current next step: the **escrow with no-funds preview**, not another image probe.
See `../verification/ESCROW_PREVIEW_HANDOFF.md`. Historical image probes below
must not be deployed again; v3 has completed its PNG diagnostic sequence.

**For the new reusable PNG diagnostic, use `IMAGE_PROBE_HANDOFF.md` and
`FilterProofImageProbe.py`.** This document retains the old WebP probe history.

Update: deployed at `0x9D1F3F657530C83500669ddBFa65568F6A185c18`, exact source
verified. Remote unsigned leader simulations reproduced `INVALID_IMAGE` for
the hardcoded WebP; control, fetch and no-image text/JSON work. No signed test
transactions were needed. Do not deploy this same historical WebP probe again.
See `../verification/VISION_DIAGNOSIS.md`. Instructions below describe the
original handoff, not a new deployment request.

Diagnostic-only source: `FilterProofVisionProbe.py`.
SHA-256: `5f5f1649e791f1eb30f1c3a39ab34662141642ef727bc8fefcf5cb8654b704c5`.

Deploy this file in the same GenLayer Studio environment as the failing escrow.
The user performs deployment. Constructor has **no arguments**. Set attached
Value to **0**. There is no payable entry point, funding or withdrawal workflow.
Network transaction fees, if applicable, are separate from attached value.
Do not deploy `contracts/FilterProofEscrow.py` yet.

After deployment, return the contract address and preferably deployment hash.
Before testing, verify finalized deployment, exact source bytes/hash and the
`info()` value:

`FilterProofVisionProbe-v1|DIAGNOSTIC_ONLY|NO_SERVICE_VERDICT|SEND_ZERO_VALUE`

## Bounded diagnostic sequence

Every call uses `run(case)` and attached Value 0. No automatic retries or loops.
Preserve each transaction hash before polling. Reconcile the same hash if a
call times out. Inspect execution/consensus and stdout/stderr, not finality alone.

| Case | What is isolated |
| --- | --- |
| `control` | No fetch, no AI, deterministic `CONTROL_OK` |
| `fetch` | Three original commit-pinned WebP images, exact byte hashes, no AI |
| `text` | No images; default text response format |
| `json` | Same prompt, no images; JSON response format |
| `one-text` / `one-json` | Same BEFORE image; only response format differs |
| `two-text` / `two-json` | Same BEFORE + AFTER bytes; only response format differs |
| `detail-json` | AFTER + SERIAL/GAUGE detail, JSON response |

Start with `control`, then `fetch`, then text/JSON controls. Do not blindly run
the remaining matrix after failure. Inspect the first failure and choose only
the matching control needed to distinguish its cause. No escrow is funded.

`FILTERPROOF_PROBE_STAGE` logs mark FETCH, FETCH_VERIFIED, EXEC_PROMPT,
MODEL_RETURNED, PARSE and COMPLETE. Errors intentionally propagate with their
runtime traceback rather than being converted to `UNCERTAIN`. Review receipts
for provider-sensitive diagnostics before committing or publicly publishing.

Normal validators independently repeat the probe and compare diagnostic case,
completion, image count and output type. Descriptive text is informational,
not byte-for-byte consensus-bound. A round-trip success is **not** evidence of
correct image interpretation, a confirmed service or an escrow happy path.
If leader-only execution is deliberately used to isolate one provider, label
that evidence as leader-only, never multi-validator consensus.

## Local evidence

- 21 probe tests, 50 existing escrow tests; combined 71 pass.
- GenVM lint, validation, schema (two public methods) and SDK typecheck pass.
- Same pinned runner/SDK as the historical two-image deployment.
- Real public downloads on 2026-09-03: BEFORE 242002 bytes, AFTER 197508 bytes,
  detail 174152 bytes; all HTTP 200 with exact SHA-256 matches. These developer
  machine checks do not establish validator-side fetch success.
- Probe has not been deployed or live-tested by the assistant.

Tests cover all cases, exact SDK image payloads, input/value guards, wrong
image bytes, provider errors, malformed output, independent validator failure
and disagreement. There are no new secrets, keys or frontend changes.
