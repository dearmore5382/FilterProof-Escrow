# FilterProof Escrow — locked specification

## Actors and immutable inputs

- `operator`: transaction sender that creates the order and receives refunds.
- `technician`: non-zero address fixed when the order is created; only this address submits proof.
- Any address may assess ready proof, execute an authorized payout/refund, or recover an expired funded order.
- Immutable order inputs: title, site code, asset serial, required filter manifest, technician, bounty, recovery timestamp.

## Lifecycle

`DRAFT -> FUNDED -> PROOF_READY -> RELEASE_AUTHORIZED -> PAID`

First non-confirming proof: `PROOF_READY -> CORRECTION_REQUIRED -> PROOF_READY`.

Second non-confirming proof: `PROOF_READY -> REFUND_AUTHORIZED -> REFUNDED`.

At/after recovery time, `FUNDED | PROOF_READY | CORRECTION_REQUIRED -> EXPIRED_REFUNDED`.

A DRAFT may be cancelled by its operator. There are exactly two append-only proof attempts.

## Proof manifest

The submitted manifest URL must be canonical HTTPS with no credentials, fragment, query string, non-default port, localhost, or IP-literal host. Its expected SHA-256 is exactly 64 lowercase hex characters.

Fetched JSON must contain exactly:

`schema`, `job_id`, `site_code`, `asset_serial`, `technician`, `service_date`, `installed_filters`, `pressure_before_kpa`, `pressure_after_kpa`, `before_image_url`, `after_image_url`, `serial_gauge_image_url`, `before_image_sha256`, `after_image_sha256`, `serial_gauge_image_sha256`, `notes`.

Each image has its own SHA-256 commitment. All three hashes must be distinct; fetched bytes must match. Distinct URLs alone do not prove distinct or immutable images.

`schema` must equal `filterproof-service-v1`; job, site, serial, technician and installed filters must match sealed inputs. The three image URLs obey the same canonical HTTPS policy and must be distinct. Manifest bytes are limited to 12,000; each image is limited to 4 MB.

## Closed visual observations

- `binding_status`: `MATCH | MISMATCH | UNAVAILABLE` (computed from bytes and sealed fields, never by AI)
- `asset_identity`: `MATCH | MISMATCH | UNCERTAIN`
- `filter_replacement`: `COMPLETE | INCOMPLETE | UNCERTAIN`
- `before_after_continuity`: `CONSISTENT | INCONSISTENT | UNCERTAIN`
- `pressure_evidence`: `PLAUSIBLE | IMPLAUSIBLE | UNCERTAIN`
- `tamper_signal`: `NONE | PRESENT | UNCERTAIN`

AI must not return payment, refund, beneficiary, verdict, or prose.

## Deterministic precedence

1. `binding_status=MISMATCH` -> `MATERIAL_FAILURE / MANIFEST_BINDING_MISMATCH`.
2. `asset_identity=MISMATCH` -> `MATERIAL_FAILURE / WRONG_ASSET`.
3. `filter_replacement=INCOMPLETE` -> `MATERIAL_FAILURE / FILTER_SET_INCOMPLETE`.
4. `before_after_continuity=INCONSISTENT` -> `MATERIAL_FAILURE / DISCONTINUOUS_EVIDENCE`.
5. `pressure_evidence=IMPLAUSIBLE` -> `MATERIAL_FAILURE / IMPLAUSIBLE_PRESSURE`.
6. `tamper_signal=PRESENT` -> `MATERIAL_FAILURE / TAMPER_SIGNAL_PRESENT`.
7. `binding_status=UNAVAILABLE` or any `UNCERTAIN` -> `INSUFFICIENT_EVIDENCE / EVIDENCE_UNAVAILABLE|VISUAL_UNCERTAINTY`.
8. Otherwise -> `SERVICE_CONFIRMED / ALL_CHECKS_CONFIRMED`.

Substantive failure always beats uncertainty. Validators independently fetch, hash, validate, and inspect evidence. Consensus compares derived verdict and reason because both control lifecycle and funds; raw leader observations are informational audit data.

## Economic and persistence invariants

- Funding must equal the positive bounty exactly.
- `held + paid + refunded == bounty` after funding.
- Terminal orders hold zero.
- State/accounting mutate before external transfer.
- One attempt has one immutable URL/hash and one immutable assessment.
- A failed fetch/model parse maps to insufficient evidence, never a confirmed service or substantive accusation.
- Validator disagreement commits no state.
- A terminal or already-assessed call cannot invoke the model again.

## Frontend protocol

All application-authored frontend copy is English-only: navigation, labels, placeholders, validation errors, transaction statuses, accessibility text and metadata. Set the document language to `en`. User-supplied evidence content is preserved as entered.

The DApp refuses writes until `VITE_CONTRACT_ADDRESS` is a non-zero address. It displays contract/network identity, uses the supplied logo, never stores private keys, and journals pending writes in local storage. A transaction is successful only after FINALIZED, accepted consensus, successful execution, and authoritative readback. Refresh resumes polling the existing hash instead of resubmitting.
