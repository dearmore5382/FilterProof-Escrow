# Vision diagnosis — 2026-09-03

## Update: WebP rejection reproduced on the deployed probe

Probe `0x9D1F3F657530C83500669ddBFa65568F6A185c18` has exact source SHA-256
`5f5f1649e791f1eb30f1c3a39ab34662141642ef727bc8fefcf5cb8654b704c5` and the expected `info()` value.

Unsigned `sim_call` **write simulations on this existing deployment** work.
This is distinct from the previously failing constructor/deploy simulation.
No transactions were signed or broadcast and no funds were attached.

| Probe | Actual remote result |
| --- | --- |
| control | SUCCESS / CONTROL_OK |
| fetch | SUCCESS / all three WebP files fetched and hash-verified |
| text, no images | SUCCESS / returned str, parsed, MODEL_ROUNDTRIP |
| json, no images | SUCCESS / returned dict, MODEL_ROUNDTRIP |
| one-text, same BEFORE WebP | ERROR at exec_prompt / NondetException with causes INVALID_IMAGE |
| one-json, same BEFORE WebP | Same error observed; first failure predates error-receipt saving |

The exact failing frame is `_decode_nondet` in the pinned SDK; the module
returns `{'causes': ['INVALID_IMAGE'], 'ctx': {}}`. No `MODEL_RETURNED` stage
is emitted for the image cases. See `probe-simulation-results.json` for the
allowlisted trace and decoded outputs. These are **leader simulations**, not
finalized transactions or multi-validator semantic consensus.

The public [GenVM image sniffer](https://github.com/genlayerlabs/genvm/blob/main/modules/implementation/src/llm/prompt.rs)
recognizes PNG (`89 50 4E 47 0D 0A 1A 0A`) and JPEG (`FF D8 FF E0`), not
WebP's RIFF header. Its [prompt handler](https://github.com/genlayerlabs/genvm/blob/main/modules/implementation/src/llm/handler.rs)
returns exactly `INVALID_IMAGE` on sniff failure before dispatching the prompt.
This corroborates the remote result; it is not an attestation of the server's
exact build. JSON without images works, so disabling JSON or changing the
consensus strategy is not supported as a remedy for this failure.

Preparing compressed WebP fixtures was an implementation mistake. Browser
support and successful HTTP/hash checks did not establish GenVM compatibility.
The older three-image PNG attempt also exceeded the documented image-count
limit, but its original swallowed exception was not recovered.

### Applied correction

- Preserve the original PNG images. Their exact bytes are already public at
  GitHub commit `56ca76cb35b4835f2d64b30cdce49aecc80c2942`; all three returned
  HTTP 200 and matched local bytes. No new image generation or editing.
- `fixtures/synthetic-happy/manifest-png.json` binds these PNGs. Local manifest
  SHA-256 is `86485db8bee70704cab541cd99132bdb9a9eae77d1779a8dcaa711efaa6ef620`.
  This new manifest has not been uploaded/published.
- Frontend and CLI manifest builder check actual file signatures. Contract
  detects unsupported committed formats before model calls and enables the
  normal correction/refund flow. A newly submitted PNG proof can replace a
  failed WebP attempt; it cannot change an old immutable commitment.
- Preserve two-image paired inspection, independent consensus and substantive
  decision rules. Do not substitute a forced positive model response.
- 72 Python tests, 11 frontend tests, lint, typechecks and frontend build pass.

### Remaining validation

The deployed probe intentionally hardcodes historical WebP bytes and cannot
test new PNG bytes. A PNG visual round trip and the escrow's actual happy path
are **not yet verified**. Do not rerun this WebP matrix, claim payout success,
or publish a release. The next live check must use the corrected PNG inputs,
with source/fixture parity established before any escrow funding.

The earlier investigation below is retained as history and is superseded by
this update where it described the WebP root cause as unknown.

## Proven facts, not inferred root causes

- Both historical deployments returned non-confirming visual observations and
  were subsequently refunded. Original receipts remain unchanged in this folder.
- Earlier broad exception handling returned the exact same all-UNCERTAIN object
  for provider/SDK errors, invalid JSON/schema and a valid uncertain model answer.
  Consequently those historical receipts cannot identify the original exception.
- The exact pinned SDK eagerly resolves `exec_prompt`; the Lazy API is not an
  explanation for string conversion failure. Its public API supports `images`
  and `response_format="json"`. Local tests capture the actual host payload,
  not a replacement for the SDK function.
- Official [Calling LLMs](https://docs.genlayer.com/developers/intelligent-contracts/features/calling-llms)
  documents a two-image limit and JSON output. The original three-image call
  violates that limit. This does not explain the subsequent two-image failure.
- No evidence establishes that `response_format="json"` is incompatible with
  the deployed runtime. The speculative removal was reverted to the documented
  API. No runner migration or source-host switch was made.

## Read-only diagnostic attempts

RPC: `https://studio.genlayer.com/api`; no key, signature, value transfer or
on-chain transaction was used.

1. `gen_dbg_traceTransaction` for
   `0xd1900e60b97e0b897727bd8db42ae3dc57092cd4ebf30c9d6fb4216d20e5dee6`
   returned HTTP 200 with RPC error `-32601`,
   `Method not found: gen_dbg_traceTransaction`.
2. `sim_call` with a disposable constructor probing text-only JSON returned
   `{"code":-32603,"message":""}`. No usable execution receipt was returned.
3. A control constructor with **no model call and no fetch** returned the same
   empty internal error. Thus this simulation failure is not evidence of a
   JSON/image incompatibility. Compatibility of this simulation mode with the
   hosted Studio is unestablished.
4. `gen_getContractCode` before/after the control returned unchanged bytes with
   SHA-256 `d9c9843009c1ee9810302957bcaf9650c305e0ccf7dbf3f5283c7abaffad5bc6`
   for `0x3512b8E2343A59c1AC5314F6d52c4fd0F26079c2`.

The reproducible script is `vision_probe.py`. It has a two-method RPC allowlist
and does not implement signing/broadcast. Its simulation `type=deploy` is not
an on-chain deployment. Its permissive probe validator is diagnostic-only,
must never authorize escrow, and is not consensus evidence. Do not rerun the
image matrix until the no-model control produces a usable receipt.

## Local fixes and verification

- Every committed image now reaches vision in two pairs. Detail negative or
  uncertain observations cannot be overridden by a positive overview.
- No prompt asserts that identity/gauges are visible before inspecting them.
- Runtime errors emit `OVERVIEW_MODEL_CALL_ERROR` or `DETAIL_MODEL_CALL_ERROR`.
  Malformed output emits the corresponding `*_MODEL_OUTPUT_INVALID`. Logs
  contain only a fixed stage/code and exception class, not raw provider details.
- These technical failures abort assessment before state mutation. The same
  READY attempt can be evaluated later; valid uncertain observations still use
  the original correction/refund flow. Existing expiry recovery is unchanged.
- Custom independent consensus and exact byte commitments remain intact.
- 50 local tests pass, including exact SDK payload capture, both runtime error
  positions, same-proof recovery, third-image veto and validator divergence.
  GenVM lint, validation and SDK typecheck pass. These use mock provider outputs.

## Earlier blocker (superseded for the WebP failure)

A standalone manual-deployment probe is now prepared at
`../diagnostics/FilterProofVisionProbe.py`; see `../diagnostics/README.md` for
the locked source hash and bounded live sequence. It passes 21 local tests,
GenVM lint/validation/typecheck. Combined local suite: 71 passing tests.
Only this diagnostic handoff is ready, not the escrow release.

The historical live vision cause and real happy path are still unconfirmed.
Needed next: a working runtime trace/simulation with actual error details, or
a user-approved no-funds diagnostic deployment on the same Studio runtime.
Only then lock and deploy an escrow revision and run the original happy,
failure and adversarial live matrix. Do not change expectations or fixtures
simply to obtain a positive result. Frontend live writes remain disabled.
