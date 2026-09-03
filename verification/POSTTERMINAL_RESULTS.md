# Post-terminal paid-state checks

Contract: `0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29`

Four unsigned, zero-value leader snapshot simulations were executed once
against the finalized PAID job. No signed transaction or transfer was sent.

| Case | Exact result | State effect |
| --- | --- | --- |
| Assessment replay | `PROOF_NOT_READY` | None |
| Duplicate release | `RELEASE_NOT_AUTHORIZED` | None |
| Refund after payment | `REFUND_NOT_AUTHORIZED` | None |
| Late proof submission | `PROOF_NOT_ALLOWED` | None |

The job, attempt, counts and accounting readbacks were byte-for-byte identical
before and after the matrix. Machine-readable evidence is in
`postterminal-0xf99765498d9f2df004ce5b117b78fb5ebb68cd29.json`.

## Evidence boundary

These results establish deterministic behavior of the deployed code on one
leader snapshot. They are not submitted transactions, validator votes or
multi-validator consensus evidence. They do not complete the remaining
failure, recovery, cross-job, concurrency or browser-wallet audit matrix.
