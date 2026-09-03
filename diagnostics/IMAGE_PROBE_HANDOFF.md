# Reusable image probe v2 — ready for user deployment

Latest candidate: **v3**, see `IMAGE_PROBE_V3_HANDOFF.md`. This file preserves
the v2 deployment and results; do not deploy v2 again for the response guard fix.

Update 2026-09-03: user deployed at
`0x767a4a1b0549f298c12A74f4CF5ce810d729cA83`. Control/fetch/one-json passed;
two-json returned `PROBE_OUTPUT_VISIBLE`; sequence stopped. See
`../verification/PNG_PROBE_FINDINGS.md`. Commands below are the historical
planned sequence, not instructions to repeat already-checkpointed cases.

Deploy **FilterProofImageProbe.py**, not the historical FilterProofVisionProbe.py
and not the escrow. Constructor: no arguments. Attached Value: **0**.
Use the same GenLayer Studio network as the previous probe.

Source SHA-256:
`2587796193458b2aa51d20a1e6a644ce8cf9b18f8af14711940f7a47a73b8dcb`

This is a stateless diagnostic contract: no payable methods, custody,
transfers, service verdicts or settlement authority. Any applicable network
fees are separate from attached value. The user performs deployment and
returns the address. No deployment or signed test transaction was sent by
the assistant for this revision.

## Interface and limits

- `info()` must return
  `FilterProofImageProbe-v2|URL_SHA256_INPUTS|DIAGNOSTIC_ONLY|SEND_ZERO_VALUE`.
- `run(mode, urls, hashes)` accepts new URL/hash lists for each call.
- `control`: empty lists; no fetch or model.
- `fetch`: one to three files; no model.
- `text` / `json`: zero to two files, same diagnostic prompt, different
  output-format configuration. Before/after or after/detail is selected by
  the order of the submitted lists, not a hardcoded filename.
- URLs must be public raw GitHub URLs with a full lowercase 40-character
  commit or the public Pinata `/ipfs/` gateway. Arbitrary hosts, URL credentials,
  query strings, fragments, encoded paths and traversal are rejected.
- Digests: exactly 64 lowercase hex characters, one per URL. Duplicate URLs
  or digests are rejected. Each fetched file must be nonempty and at most 4 MB.
- All bytes are independently fetched and SHA-256 checked before a model call.
  The known runtime accepts the PNG signature or JPEG `FF D8 FF E0`; use PNG.
  Signature checks do not prove full decoding or physical authenticity.
- Errors remain visible with a fixed last-stage log and real traceback.
- Normal validators independently execute the same call and compare input
  binding and diagnostic completion. Free descriptions are informational;
  this is not semantic approval of a service.

## Predefined PNG sequence after deployment

Use the existing `fixtures/synthetic-happy/manifest-png.json` as the **local
argument source**, not a fetched manifest. It need not be uploaded to test
this probe. Its three original PNG files already exist at full GitHub commit
`56ca76cb35b4835f2d64b30cdce49aecc80c2942`. No image conversion is performed.

Run from the repository root, with the actual v2 address:

```powershell
python -m diagnostics.run_image_probe preflight --contract <V2_ADDRESS>
python -m diagnostics.run_image_probe control --contract <V2_ADDRESS>
python -m diagnostics.run_image_probe fetch --contract <V2_ADDRESS>
python -m diagnostics.run_image_probe one-json --contract <V2_ADDRESS>
python -m diagnostics.run_image_probe two-json --contract <V2_ADDRESS>
python -m diagnostics.run_image_probe detail-json --contract <V2_ADDRESS>
```

Execute one command at a time, not as an automatic batch. Stop at failure;
choose `json` (no images), `text` or matching `one-text` / `two-text` only
when needed to isolate the fault. Do not change expected results to make
failures pass. Changing fixtures uses `--fixture <local-manifest.json>`;
same contract, new input-binding digest, no redeployment required.

The runner has no signing, broadcasting or deployment method. It checks
exact deployed source and `info()` before a single `sim_call`. It saves intent
first and refuses a repeated case with the same input-binding digest. A timeout
or failed simulation stays recorded and does not trigger automatic retries.
Node configuration and sensitive key fields are stripped before checkpoints.
Review any provider traceback before publishing. No snapshot is committed
automatically.

## Local verification / honest scope

- 45 v2 contract tests: mode and ordered-image payloads, URL/hash/count/value
  guards, runtime format, size/status/hash failures, provider/JSON errors,
  independent validator mismatch and changed bytes.
- Three runner tests: case mapping, zero-value/RPC allowlist, sensitive config
  removal and result decoding.
- Full Python suite: **120 passed** (72 existing + 48 new).
- GenVM lint, validation/schema and SDK typecheck pass on the same pinned runner.
- Frontend and escrow unchanged in this v2-probe turn; prior results remain
  scoped to their documented revisions.
- **PNG one-image remote simulation passed; two-image diagnostic guard failed.** A simulated round trip is not an on-chain
  transaction, multi-validator consensus, escrow semantic PASS or payout proof.
- After PNG transport passes, verify the actual assessment logic before
  the user deploys an escrow revision and funds a minimal live lifecycle test.
