# FilterProof Escrow

A focused GenLayer DApp for hash-bound evidence of commercial water-filter cartridge replacement. An operator seals the system identity, assigned technician, filter set, bounty and recovery deadline. The technician submits a manifest and three separately hash-bound images. Validators independently retrieve the evidence and produce closed observations; deterministic rules control escrow authorization.

## Current status

**Deployed preview and one funded synthetic happy path passed. Full adversarial audit has NOT passed. Not a production-ready water-safety or payment service.**

Cloudflare frontend: https://filterproof-escrow.dearmorescheuer5382.workers.dev

- Contract and local test suite implemented.
- The escrow at `0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29` passed all four frozen unsigned preview cases using its actual classifier; the current local suite has 201 passing tests. See `verification/ESCROW_PREVIEW_RESULTS.md`. No funds were sent by the preview sequence.
- The same escrow completed one explicitly authorized 0.1 GEN testnet lifecycle: five finalized majority-agree writes, SERVICE_CONFIRMED, PAID, exact child transfer and zero ending contract balance. See `verification/FUNDED_HAPPY_PATH.md`. The fixture is synthetic and the remaining adversarial matrix is open.
- Four unsigned zero-value post-terminal simulations rejected assessment replay, duplicate release, refund after payment and late proof as expected, with identical before/after state. This is leader-snapshot evidence, not consensus evidence.
- A separate zero-value draft smoke test finalized create/cancel with majority agreement and ran eight unsigned failure simulations for authority, exact funding and premature actions. State and public balances remained unchanged. See `verification/FAILURE_SMOKE_RESULTS.md`; F1–F3 remain only partially closed because the negative calls were simulations.
- A 0.01 GEN binding-failure lifecycle finalized all seven parent writes with majority agreement: two append-only mismatched-digest attempts led to REFUND_AUTHORIZED, then exactly one child transfer returned the full escrow to the operator. See `verification/REFUND_PATH_RESULTS.md`; this closes live-matrix F6 for the declared scenario.
- A separate 0.01 GEN expiry lifecycle rejected early recovery in simulation, then accepted a permissionless recovery from the technician wallet after deadline. The finalized child transfer returned the full escrow and left contract balance zero. See `verification/EXPIRY_RECOVERY_RESULTS.md`; this closes F7 for a funded job with no proof.
- Unsigned source-failure previews for a pinned 404 and a pinned oversized response both failed closed as `INSUFFICIENT_EVIDENCE / EVIDENCE_UNAVAILABLE` with unchanged state. See `verification/SOURCE_FAILURE_PREVIEW_RESULTS.md`; F4 remains partial.
- English-only frontend with supplied logo, local proof preparation, guarded wallet workflows and persistent transaction reconciliation.
- The frontend identifies the source-verified Studionet contract but keeps all live writes disabled while `liveAuditVerified` remains false.
- Public-source negative/ambiguous fixtures found and HTTP/hash checked. A repository-owned synthetic positive triplet is included and explicitly labeled; it is not a real-world service record.
- Two earlier deployments were tested and refunded after non-confirming assessments; see `verification/AUDIT.md` and the original receipt files. Neither is a release candidate.
- The current revision checks all three images in two calls and preserves proof on model runtime/schema errors. Actual escrow positive preview returned SERVICE_CONFIRMED and the funded happy lifecycle finalized with majority agreement. The remaining live adversarial matrix is open.

## Run locally

Requirements: Python 3.12+, `genlayer-test`, `genvm-linter`, and Node 22.13+.

```powershell
python -m pytest -q
$env:PYTHONIOENCODING='utf-8'
genvm-lint check contracts/FilterProofEscrow.py
genvm-lint typecheck contracts/FilterProofEscrow.py
cd frontend
npm ci
npm test
npm run typecheck
npm run lint
npm run build
npm run dev
```

`npm run lint` checks application-authored source and tests. The scaffold's unmodified component catalog is not included in that lint scope; the complete project still receives TypeScript checking.

## Evidence workflow

1. Create a work order and fund its exact bounty after deployment.
2. In Proof Studio, enter the sealed identity/filter fields and pressure readings; choose three distinct original image files and their public HTTPS URLs.
3. Download the exact JSON manifest. Host the JSON and the original images without transformations. Hashes bind bytes, not the authenticity of the service.
4. Submit the manifest URL and computed SHA-256 as the assigned technician.
5. Assess, correct once if needed, then execute authorized payout/refund. Expired unresolved orders have a refund recovery path.

Do not publish private customer information. Public evidence is not confidential. Do not use real funds with this unverified testnet build.

## Documentation

- `PLAN.md`: staged delivery and stop condition.
- `SPEC.md`: state machine, exact evidence fields and precedence.
- `verification/AUDIT.md`: reproducible findings and honest test boundaries.
- `verification/DEPLOYMENT_READINESS.md`: remaining release gates.
- `verification/LIVE_MATRIX.md`: predefined post-deployment cases.
- `fixtures/public-source-registry.json`: publisher URLs, byte commitments and provenance limitations.

## Key limitations

No physical capture attestation, technician licensing verification, lab water-quality measurement or drinking-water certification. Independent AI observations can still be wrong. A SHA-256 match does not prove that a photograph depicts genuine work. Direct Mode does not verify network consensus or emitted transfers. The real wallet/receipt path remains unverified until the user deploys and the live matrix passes.
