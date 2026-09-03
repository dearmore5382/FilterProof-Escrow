# PNG probe v3 — remote diagnostic sequence passed

User-deployed address: `0x9Bed86f3ccf45b778c09e33A91aD14e5C65c3857`.
Exact source bytes and v3 info verified before every simulation:
`9c20d05aa62bc52d0e4280af6789dcd745675eaee0a986f8b209d19ced605ddf`.

Evidence: `image-probe-0x9bed86f3ccf45b778c09e33a91ad14e5c65c3857-results.json`.
Each record includes UTC start time, exact arguments, source hash, returned
value and stage logs. Node configuration and other sensitive fields are omitted.

| Frozen case | Execution | Observed diagnostic result |
| --- | --- | --- |
| control | SUCCESS | CONTROL_OK |
| two-json: before/after | SUCCESS | Both PNG hashes verified; model dict parsed; visible length 127; binding/count readback matched |
| detail-json: after/serial | SUCCESS | Both PNG hashes verified; model dict parsed; visible length 37; binding/count readback matched |

Each case ran once, without retries, source changes or fixture substitutions.
All three original synthetic PNG files were covered across the two pairs.
The fixed fixtures remain pinned at GitHub commit
`56ca76cb35b4835f2d64b30cdce49aecc80c2942`.

The overview model description mentions FP-TEST-001, DEMO-SITE-01, pressure
200 kPa before and 300 kPa after, and new cartridges. The detail description
mentions FP-TEST-001 and 300 kPa. These are informational descriptions of
synthetic test images, not an independently verified physical service.

## Scope and remaining gates

These are **remote unsigned leader snapshot simulations**, not on-chain
transactions or multi-validator consensus evidence. No signed transaction,
custody change or funds transfer was made by this sequence. Historical v2
failure evidence and source are preserved; v3 success does not reveal the
unknown exact length of the failed v2 response.

This closes the planned PNG transport/JSON/diagnostic-parser sequence. It
does not test the escrow's actual closed-field observations, deterministic
verdict derivation, lifecycle or payout. Next: verify the actual escrow
assessment logic against the locked synthetic positive and negative matrix
in a no-funds setting before asking the user to deploy/fund a final escrow.
The exact PNG manifest is still local; publication is needed before the
escrow workflow. Do not wire this probe address into the frontend.
