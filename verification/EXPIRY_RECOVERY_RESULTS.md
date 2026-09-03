# Expiry recovery path — verified on Studionet

Contract: `0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29`

A synthetic job locked 0.01 GEN until `2026-09-03T09:48:16Z`. Before the
deadline, an unsigned leader simulation returned exactly
`RECOVERY_TOO_EARLY` and left state unchanged. After the deadline, the
technician wallet—not the operator—called the permissionless recovery method.

| Step | Transaction | Final result |
| --- | --- | --- |
| Create job 3 | `0x542afaaaca44d3f96e4ff5f836f934802ee0e84df2865fa46d660228927b5b31` | FINALIZED / MAJORITY_AGREE / DRAFT |
| Fund 0.01 GEN | `0xcf1930fd732c2b41c0b8d3e29e493b59e3b654afd7b067b8af3ae156f9233668` | FINALIZED / MAJORITY_AGREE / FUNDED |
| Recover after deadline | `0x91885224cbe9604306d8877f8750b5ce751dc82516887cb6dde5db94343015e8` | FINALIZED / MAJORITY_AGREE / EXPIRED_REFUNDED |

Exactly one finalized child transaction
`0x767aa2183840a20cb1ae8c561f6bb8479ed1294db14cd10db28c5ff6a22d3835`
returned 0.01 GEN from the escrow to the operator. The operator balance rose by
exactly 0.01 GEN across recovery. Final accounting is bounty 0.01 GEN, held 0,
paid 0, refunded 0.01 GEN; contract balance is 0.

Machine-readable sanitized evidence:
`expiry-recovery-0xf99765498d9f2df004ce5b117b78fb5ebb68cd29.json`.

## Evidence boundary

This closes live-matrix F7 for a funded job with no proof. The early-recovery
result is leader simulation evidence, while the post-deadline recovery and
child transfer are finalized consensus evidence.
