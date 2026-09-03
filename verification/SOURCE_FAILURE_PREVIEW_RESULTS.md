# Source-failure preview results

Two unsigned, zero-value leader previews ran once against exact deployed source:

| Case | Outcome |
| --- | --- |
| Pinned GitHub URL returning HTTP 404 | `INSUFFICIENT_EVIDENCE / EVIDENCE_UNAVAILABLE` |
| Pinned 23,670-byte source exceeding the 12,000-byte manifest limit | `INSUFFICIENT_EVIDENCE / EVIDENCE_UNAVAILABLE` |

Both returned binding `UNAVAILABLE`, all visual fields `UNCERTAIN`, and scope
`PREVIEW_ONLY_NO_PAYMENT_AUTHORIZATION`. Counts and finalized state were
identical before and after. No transaction was signed and no GEN was attached.

Machine evidence:
`source-failure-preview-0xf99765498d9f2df004ce5b117b78fb5ebb68cd29.json`.

These results partially cover F4. Empty, 429 and 5xx sources remain untested,
and unsigned leader previews are not multi-validator consensus evidence.
