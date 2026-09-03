# Predefined live verification matrix

Do not run before the user deploys the reviewed source. Never deploy automatically. Use fresh testnet-only wallets and small test amounts. Do not reuse private keys from other projects or put private keys in frontend configuration.

## Prerequisites

1. Positive visual fixture: use the repository-owned, clearly labeled synthetic triplet in `fixtures/synthetic-happy`. It must never be described as a real service record.
2. Public exact-byte manifest hosting plus image URL/hash preflight through the same acquisition path as validators. Development-machine HTTP success alone is insufficient.
3. Source candidate hash recorded and local gates rerun after any source change.
4. User deployment transaction finalized; deployed code bytes match the candidate SHA-256; initial counts are `0|0`.

## Matrix

| ID | Group | Sequence | Expected |
| --- | --- | --- | --- |
| H1 | Happy | Create → fund exact bounty → submit complete proof → assess → release | Exact return IDs; RELEASE_AUTHORIZED then PAID; technician receives payout |
| H2 | Happy remediation | Incomplete proof → first assessment → corrected proof → second assessment → release | Append-only first attempt; correction does not overwrite history |
| F1 | Failure | Wrong operator funds; wrong technician submits | Funding reverts; no custody/attempt mutation |
| F2 | Failure | Underfund and overfund | Revert, operator balance/custody evidence recorded |
| F3 | Failure | Assess before proof; payout before authorization | Business rejection, unchanged state |
| F4 | Failure | Empty/404/429/5xx/oversized source | No payment authorization; insufficient evidence where retrieval fails |
| F5 | Failure | Mismatched manifest digest; wrong image hash | Binding mismatch; no release |
| F6 | Failure | Two non-confirming attempts then refund | REFUND_AUTHORIZED → REFUNDED, operator receives escrow |
| F7 | Failure/recovery | Fund then reach recovery deadline | Permissionless EXPIRED_REFUNDED; no later assessment or release |
| A1 | Combination | Correct manifest fields + unrelated public service images | No confirmed service solely from captions/model labels |
| A2 | Combination | Prompt injection + missing identity/pressure | No release merely due to embedded instructions |
| A3 | Combination | Substantive negative + uncertain secondary fields | Frozen precedence reason wins |
| A4 | Combination | Job-A manifest submitted to Job-B | Exact identity mismatch, no release |
| A5 | Combination | Assessment replay + duplicate settlement + attempted late proof | No repeated model call after assessment; no second payout/refund |
| A6 | Combination | Pending write → page reload → account/chain switch | Same hash retained; no automatic broadcast; mismatch blocks writes |
| A7 | Combination | Wallet interruption after submit + second tab | Persisted intent/recovery; no new submit until prior hash reconciled |

## Evidence per write

Record network/chain, contract, source hash, actor, method, exact arguments/value, transaction hash, FINALIZED status, leader execution, consensus result/votes, exact return, finalized readback and transfer effects. A business rejection is an expected negative result, not successful workflow completion.

Payout/refund checks must inspect emitted child transactions and recipient balances; parent accounting alone is insufficient. Preserve failed and pending attempts. Stop on divergent outcomes; do not rewrite expectations to match an unexpected result.

## Frontend release gate

Only after live verification, set `frontend/lib/deployment.json` with the verified address/hash and `liveAuditVerified: true`, then rebuild. Real wallet browser checks, reload/recovery and a compiled-configuration check are still required. Public/shared publishing requires the corresponding access approval.
