# Low-value failure smoke test

Contract: `0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29`

The runner first checked public balances and selected a 0.01 GEN job bounty,
but never funded the job. Only two signed zero-value writes were submitted:

| Action | Transaction | Final result |
| --- | --- | --- |
| Create draft job 1 | `0x1bebb49f8d27f34f18b7a87715cace06eb913d375c71333f9093a965c6cc53d4` | FINALIZED / MAJORITY_AGREE / job 1 |
| Cancel draft job 1 | `0x6c3f355bd495cdfda9acb335d38278f8447eae6b1904751f0b46e50439ee2e09` | FINALIZED / MAJORITY_AGREE / CANCELLED |

Between those transactions, eight unsigned leader snapshot simulations ran
once against the DRAFT job:

| Case | Exact result |
| --- | --- |
| Wrong wallet funds | `OPERATOR_ONLY` |
| Underfund | `WRONG_FUNDING_VALUE` |
| Overfund | `WRONG_FUNDING_VALUE` |
| Wrong technician submits | `TECHNICIAN_ONLY` |
| Assess before proof | `PROOF_NOT_READY` |
| Release before authorization | `RELEASE_NOT_AUTHORIZED` |
| Refund before authorization | `REFUND_NOT_AUTHORIZED` |
| Recover a draft | `RECOVERY_NOT_ALLOWED` |

The state was identical before and after all eight simulations. Final state is
job `CANCELLED`, bounty 0.01 GEN, held 0, paid 0, refunded 0, and contract
balance 0. Public operator and technician balances were also unchanged.

Machine-readable evidence:
`failure-smoke-0xf99765498d9f2df004ce5b117b78fb5ebb68cd29.json`.

## Evidence boundary

The create/cancel lifecycle is finalized consensus evidence. The eight failure
outcomes are unsigned leader simulations, not submitted negative transactions
or multi-validator consensus. They partially exercise F1–F3 but do not close
those live-matrix rows. No funding, payout or refund occurred.
