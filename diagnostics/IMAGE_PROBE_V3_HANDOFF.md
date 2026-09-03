# Image probe v3 — bounded prompt and failure diagnostics

Completed: user deployed `0x9Bed86f3ccf45b778c09e33A91aD14e5C65c3857`.
Source-verified remote control/two-json/detail-json simulations all passed.
See `../verification/PNG_PROBE_V3_FINDINGS.md`. The sequence below is retained
for reproducibility, not an instruction to repeat the completed cases.

Deploy `diagnostics/FilterProofImageProbeV3.py` manually in the same Studio
network. Constructor: no arguments. Value: **0**. Class: FilterProofImageProbe.
This is a diagnostic, not the escrow. Never configure it as the frontend escrow.

Source SHA-256:
`9c20d05aa62bc52d0e4280af6789dcd745675eaee0a986f8b209d19ced605ddf`.

## What changed and what did not

The v2 failure is recorded in `../verification/PNG_PROBE_FINDINGS.md`.
Its exact failed description was not captured, so do not claim its length.
V2 source, address and all evidence remain unchanged.

- Prompt explicitly requests **1–160 characters total across all images**,
  allows omission of secondary details, and requests UNREADABLE when necessary.
- Existing acceptance remains 1–500 characters: no relaxation, truncation,
  replacement of invalid outputs, or automatic model retries.
- Logs include serialized output character count and visible character count,
  not raw model prose. Errors distinguish EMPTY, TOO_LONG and NO_IMAGES_MISMATCH.
- URL/hash binding, PNG/JPEG checks, two-image model limit, closed schema,
  independent validator and zero-value guards are unchanged.
- `info()` identifies v3; the runner requires `--version v3` and exact source.

The model may still disobey the prompt. Local mocked tests do not establish
remote success. If it fails, stop and inspect the specific error/counts. Do
not change expected verdicts, loop until success, or fund an escrow to test it.

## Verification

2026-09-03: full local suite **177 passed**: 51 escrow, 21 historical vision
probe, 45 image v2, 45 image v3 shared regressions, 12 v3 boundary/history
tests, 3 runner tests. GenVM lint, schema/validation and SDK typecheck pass.
The runner pin is intentionally unchanged; a newer available pin is not part
of this targeted fix. Frontend and escrow unchanged in this revision.

## Frozen remote sequence after user deployment

Run one command at a time from the repository root. Stop on any failure.

```powershell
python -m diagnostics.run_image_probe preflight --version v3 --contract <V3_ADDRESS>
python -m diagnostics.run_image_probe control --version v3 --contract <V3_ADDRESS>
python -m diagnostics.run_image_probe two-json --version v3 --contract <V3_ADDRESS>
python -m diagnostics.run_image_probe detail-json --version v3 --contract <V3_ADDRESS>
```

The two image calls each re-fetch/hash the relevant PNG pair, collectively
covering all three original files. The unchanged local manifest provides
arguments. No extra standalone fetch or one-image repetition is planned.
Only unsigned `sim_call` is used; no signing, broadcast or funds. Checkpoints
prevent repetition of the same case/inputs on an address. Preserve all failures.

After these pass, the actual escrow closed-field classifier still needs its
own semantic verification and live happy/failure/adversarial lifecycle. Probe
completion is not a maintenance approval, validator-consensus proof or payout.
