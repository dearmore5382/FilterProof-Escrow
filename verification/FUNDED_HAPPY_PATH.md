# Funded synthetic happy path — verified on Studionet

Contract: `0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29`.
Chain ID: 61999. Exact deployed source SHA-256:
`326e46f225bc2e88e0cefb581a8b5cbf450f3322017993098794bdcf5d3ff2a9`.

Public machine-readable evidence:
`funded-happy-0xf99765498d9f2df004ce5b117b78fb5ebb68cd29.json`.
It contains the exact arguments, public receipts, validator votes/executions,
finalized readbacks and transfer receipt. Private keys are excluded. The
private checkpoint remains gitignored.

| Step | Transaction | Final status | Consensus / return |
| --- | --- | --- | --- |
| Create job | `0x93be313c7ebb5186bfb1023e727afc32f155383191ab664c309ed173e4ab7d6f` | FINALIZED | MAJORITY_AGREE / job 0 |
| Fund 0.1 GEN | `0x7b11c7415357a49bbd732050f976e45facaed9a410d56aa525e78c16c92cae6d` | FINALIZED | MAJORITY_AGREE / FUNDED |
| Submit proof | `0x808f2a87766aab67b108b83a61a924bec8b7790832caa58d802f34eaf49fbda1` | FINALIZED | MAJORITY_AGREE / attempt 0 |
| Assess proof | `0x551b37170600513a1b5430f42c14f1d383c4a8a95f91b2ff61f460d149a3a732` | FINALIZED | MAJORITY_AGREE / RELEASE_AUTHORIZED |
| Execute release | `0x83ebce382ad98808764259b883dbd2961e77e0ac81cf128ec88d66215469ef39` | FINALIZED | MAJORITY_AGREE / PAID |

Assessment readback is `SERVICE_CONFIRMED / ALL_CHECKS_CONFIRMED` with
binding MATCH, asset MATCH, replacement COMPLETE, continuity CONSISTENT,
pressure PLAUSIBLE and tamper NONE. Accounting ended bounty 0.1 GEN, held 0,
paid 0.1 GEN, refunded 0, contract balance 0.

Exactly one finalized child transfer
`0x0190b34ed0e8967295b413cee06a43573de4b0c35296c196ce5b815809f2dcff`
sent 0.1 GEN from the contract to technician
`0xA63DE24e30C88FB1019E8956654730316e36eDBE`. Technician balance increased
from 101.001 GEN to 101.101 GEN, exactly 0.1 GEN.

The operator explicitly authorized this single 0.1 GEN testnet lifecycle.
Every parent write was sent once and its hash checkpointed immediately; no
automatic resubmission, correction attempt or source/fixture substitution.

## Honest limits

The fixture is synthetic and explicitly labeled, not real maintenance or
water-safety evidence. This proves one happy path on the configured Studionet,
not production security or the complete adversarial matrix. Failure/recovery,
unavailable-source, multi-job, browser-wallet and concurrent-tab cases remain.

Four zero-value unsigned leader simulations were subsequently run against the
final PAID snapshot. Assessment replay returned `PROOF_NOT_READY`, duplicate
release returned `RELEASE_NOT_AUTHORIZED`, refund after payment returned
`REFUND_NOT_AUTHORIZED`, and late proof returned `PROOF_NOT_ALLOWED`. Exact
before/after readbacks were identical. See
`postterminal-0xf99765498d9f2df004ce5b117b78fb5ebb68cd29.json`. These are snapshot
simulations, not submitted transactions or multi-validator consensus evidence.
