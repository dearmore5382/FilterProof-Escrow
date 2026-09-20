# Steward production-flow response

The verified StudioNet configuration is enabled in the public frontend for
contract `0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29`. Its deployed source matches
the repository contract at SHA-256
`326e46f225bc2e88e0cefb581a8b5cbf450f3322017993098794bdcf5d3ff2a9`.

## Complete live flow

The published funded lifecycle used two test wallets and completed all required
steps with finalized multi-validator consensus and authoritative readback:

| Step | Transaction | Result |
| --- | --- | --- |
| Create work order | [0x93be…d6f](https://explorer-studio.genlayer.com/transactions/0x93be313c7ebb5186bfb1023e727afc32f155383191ab664c309ed173e4ab7d6f) | Job `0`, `DRAFT` |
| Fund exactly 0.1 GEN | [0x7b11…e6d](https://explorer-studio.genlayer.com/transactions/0x7b11c7415357a49bbd732050f976e45facaed9a410d56aa525e78c16c92cae6d) | `FUNDED` |
| Technician submits proof | [0x808f…da1](https://explorer-studio.genlayer.com/transactions/0x808f2a87766aab67b108b83a61a924bec8b7790832caa58d802f34eaf49fbda1) | Attempt `0`, `PROOF_READY` |
| Assess proof | [0x551b…732](https://explorer-studio.genlayer.com/transactions/0x551b37170600513a1b5430f42c14f1d383c4a8a95f91b2ff61f460d149a3a732) | `RELEASE_AUTHORIZED` |
| Execute payout | [0x83eb…f39](https://explorer-studio.genlayer.com/transactions/0x83ebce382ad98808764259b883dbd2961e77e0ac81cf128ec88d66215469ef39) | `PAID` |
| Native child transfer | [0x0190…cff](https://explorer-studio.genlayer.com/transactions/0x0190b34ed0e8967295b413cee06a43573de4b0c35296c196ce5b815809f2dcff) | 0.1 GEN credited to technician |

Final readback for job `0` is `PAID`: bounty 0.1 GEN, held 0, paid 0.1
GEN, refunded 0. The payout parent emitted exactly one finalized native child
transfer, linked by `triggered_by`, from the contract to the assigned technician
for the exact bounty. The contract balance was zero at completion.

The separately documented binding-mismatch path reaches `REFUND_AUTHORIZED`
after two immutable failed attempts and returns the exact 0.01 GEN escrow to the
operator through one finalized native transfer. See [REFUND_PATH_RESULTS.md](REFUND_PATH_RESULTS.md).

## Additional reviewer wallet evidence

A fresh browser-wallet run created Job `4` and funded its exact 0.001 GEN
bounty. Both transactions finalized with unanimous 5/5 validator agreement:

- [Create Job 4](https://explorer-studio.genlayer.com/transactions/0xe40688fddf687aaee5b0992802ae158373099a2f207428e31ea66265e04cea52)
- [Fund Job 4](https://explorer-studio.genlayer.com/transactions/0x4be64f414f5510bc5b40dffd4b48c8884c6d3db5c44d99a3778e5c22e20289da)

Latest-final readback is `FUNDED`, with bounty and held both exactly
`1000000000000000` attoGEN and paid/refunded both zero. Exact decoded calls,
votes and readback are documented in
[REVIEWER_WALLET_FLOW.md](REVIEWER_WALLET_FLOW.md) and
[reviewer-wallet-flow-job-4.json](reviewer-wallet-flow-job-4.json).

### Evidence scope clarification

The two evidence sets must not be conflated:

- **Job 0 is the complete end-to-end lifecycle evidence.** It covers creation,
  exact funding, technician proof submission, assessment,
  `RELEASE_AUTHORIZED`, payout, authoritative `PAID` accounting readback and
  the resulting finalized native transfer to the assigned technician.
- **Job 4 is additional browser-wallet evidence only.** It independently
  demonstrates that the updated public frontend connected a user wallet,
  created the intended sealed work order and funded exactly 0.001 GEN. At the
  time this response was prepared, Job 4 was `FUNDED` with zero proof attempts;
  it must not be presented as another completed lifecycle.

The current contract balance of 0.001 GEN belongs to the held Job 4 bounty.
It is not residue from the completed Job 0 settlement. The production-readback
script continues to verify source parity, Job 0 `PAID` accounting, parent
finality/consensus and the exact native child transfer.

## UI transaction-state fix

The frontend does not treat `FINALIZED` alone as success. It verifies, in order:

1. transaction hash, sender, contract, method, arguments and attached value;
2. successful execution and majority-agree consensus;
3. the method's expected return value;
4. authoritative `get_job`, `get_attempt` and `get_accounting` readback;
5. for payout/refund/recovery, exactly one finalized native child transfer with
   the expected parent, contract sender, beneficiary, amount and credited flag.

Settlement remains `TRANSFER_PENDING` until the child is finalized. Only after
all checks pass does the journal display `TRANSFER_VERIFIED` and allow another
write. Every parent and child hash links to GenLayer Explorer.

The **Verify live payout** control is read-only and repeats source parity, PAID
accounting and child-transfer checks directly against StudioNet. It works in a
fresh browser without a wallet or local transaction journal.

## Reproduce the public readback

```powershell
python verification/verify_production_readback.py
```

The script loads no keys and cannot submit a transaction. Full machine-readable
receipts are in
[`funded-happy-0xf99765498d9f2df004ce5b117b78fb5ebb68cd29.json`](funded-happy-0xf99765498d9f2df004ce5b117b78fb5ebb68cd29.json).
