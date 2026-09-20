# Reviewer wallet flow — live Job 4

This is an additional browser-wallet production check against the deployed
contract `0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29` on StudioNet (chain 61999).
It is separate from the previously completed Job 0 lifecycle.

| Step | Explorer transaction | Finality and consensus | Verified result |
| --- | --- | --- | --- |
| Create sealed work order | [`0xe40688fddf687aaee5b0992802ae158373099a2f207428e31ea66265e04cea52`](https://explorer-studio.genlayer.com/transactions/0xe40688fddf687aaee5b0992802ae158373099a2f207428e31ea66265e04cea52) | `FINALIZED`; 5/5 validators agreed | `create_job` returned Job `4` |
| Fund exact bounty | [`0x4be64f414f5510bc5b40dffd4b48c8884c6d3db5c44d99a3778e5c22e20289da`](https://explorer-studio.genlayer.com/transactions/0x4be64f414f5510bc5b40dffd4b48c8884c6d3db5c44d99a3778e5c22e20289da) | `FINALIZED`; 5/5 validators agreed | `fund_job(4)` returned `FUNDED` with exactly 0.001 GEN attached |

Both writes were signed by operator
`0xFf36b56CcA032C559e52e2A4F20c2C594B02Fe37`. The sealed technician is
`0x1D283b45974B0be9630DFD1deC6A62a9B72B2760`.

Authoritative latest-final readback after funding:

```text
get_job(4)
FUNDED|0xFf36b56CcA032C559e52e2A4F20c2C594B02Fe37|0x1D283b45974B0be9630DFD1deC6A62a9B72B2760|Reviewer live verification|REVIEW-SITE-01|FP-REVIEW-001|SED-5M, CARBON-10, UF-01|2026-09-20T03:14:00Z|0

get_accounting(4)
1000000000000000|1000000000000000|0|0|1000000000000000
```

The accounting fields are `bounty|held|paid|refunded|contract balance`, in
attoGEN. This proves the browser wallet created the intended record and placed
the exact declared 0.001 GEN bounty into contract custody. It does not claim
that Job 4 has submitted or assessed evidence, reached payout/refund, or
completed a native transfer. The separately documented Job 0 lifecycle is the
complete end-to-end evidence.

Machine-readable facts are preserved in
[`reviewer-wallet-flow-job-4.json`](reviewer-wallet-flow-job-4.json).
