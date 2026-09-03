# Binding-failure refund path — verified on Studionet

Contract: `0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29`

A synthetic 0.01 GEN job deliberately submitted the correct public manifest URL
with an incorrect all-zero digest twice. All seven parent writes finalized with
`MAJORITY_AGREE` and every step received an authoritative readback.

| Step | Transaction | Final state / result |
| --- | --- | --- |
| Create job 2 | `0xd7d0649ee8bbc405af478a5d2e2bd1772004c3586c12fe6feaf30a606b256ffe` | DRAFT / job 2 |
| Fund 0.01 GEN | `0x69614e089d2e5fb8d8eaa226dae0c3722fdbf2b7e3079cebd629932316dd230e` | FUNDED |
| Submit attempt 1 | `0xe0b746359cc52b9910de47f224e105dc8557ca72721f217016f167849e297a02` | PROOF_READY / attempt 1 |
| Assess attempt 1 | `0xfca29eaea01f9958449e0ec57213db938c7d2227050399698aa5cd77117b8912` | CORRECTION_REQUIRED |
| Submit attempt 2 | `0x5d720cacf2b977bbe84badb3a82c0012893ca9228b51deeb4642e10e2d31d809` | PROOF_READY / attempt 2 |
| Assess attempt 2 | `0x7180fe346982bb2db45926e871a06583bc0254e6bb229fcba9b13833c46518d0` | REFUND_AUTHORIZED |
| Execute refund | `0x5ceba9aaade8dbcc722e6cb8a6df3568ccbe9cb264145bc1274d5d3dfd41429a` | REFUNDED |

Both assessment readbacks are `MATERIAL_FAILURE / MANIFEST_BINDING_MISMATCH`.
Attempt 1 remains intact after attempt 2 is appended. Exactly one finalized
child transaction
`0x27153ed8614a7eb944a40b356988957c69641cd3179bbe744d4afc5aeecd8a8b`
returned 0.01 GEN from the escrow to the operator. Operator balance increased by
exactly 0.01 GEN across settlement; final accounting is bounty 0.01 GEN, held 0,
paid 0, refunded 0.01 GEN, and contract balance 0.

Machine-readable sanitized evidence:
`refund-path-0xf99765498d9f2df004ce5b117b78fb5ebb68cd29.json`.

## Evidence boundary

This closes live-matrix F6 for the deliberately incorrect manifest digest and
also demonstrates append-only correction history. It does not establish the
other source-unavailability/image-substitution cases or recovery expiry.
