# PNG probe findings — 2026-09-03

Address: `0x767a4a1b0549f298c12A74f4CF5ce810d729cA83`.
Exact deployed source and info verified before each simulation. SHA-256:
`2587796193458b2aa51d20a1e6a644ce8cf9b18f8af14711940f7a47a73b8dcb`.

Evidence: `image-probe-simulation-results.json`. These are remote unsigned
leader snapshot simulations, not transactions, multi-validator consensus,
an escrow happy path, or payout evidence. No signed transaction or funds sent.

| Case | Observed result |
| --- | --- |
| control | SUCCESS / CONTROL_OK |
| fetch | SUCCESS / all three original PNG files fetched and SHA-256 verified |
| one-json | SUCCESS / model returned dict, parsed successfully; described asset FP-TEST-001, pressure 200 kPa and synthetic-fixture banner |
| two-json | ERROR / model returned dict, reached PARSE, then PROBE_OUTPUT_VISIBLE |
| detail-json | NOT RUN; stopped after two-json failed |

The two-image error is in the diagnostic response guard, not image decoding:
`PROBE_OUTPUT_VISIBLE` means the visible string is empty or longer than 500
characters for this image-bearing call. The probe does not save the failed
model response; the exact length and which alternative occurred are unknown.
No inference of semantic success is made merely because the model returned.

Source review identifies a diagnostic design issue: the prompt requests only
"a short description" while the parser imposes a 500-character bound. An
overlong description is plausible, but not proven from the saved receipt.
Do not relax escrow acceptance criteria or change images to force a pass.
The deployed probe source is preserved; there was no retry or redeployment.
The runner now displays decoded failure reasons instead of only `result: null`.

Next engineering step: design a bounded diagnostic response with explicit
prompt limits and useful failure-length diagnostics, or assess the actual
closed-field escrow classifier in a suitable no-funds harness. Re-run local
tests before requesting any user deployment. PNG input compatibility has
progressed; the corrected escrow's semantic and live lifecycle gates remain open.
