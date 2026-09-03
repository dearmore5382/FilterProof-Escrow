# FilterProof Escrow

A focused GenLayer DApp for hash-bound evidence of commercial water-filter cartridge replacement. An operator seals the system identity, assigned technician, filter set, bounty and recovery deadline. The technician submits a manifest and three separately hash-bound images. Validators independently retrieve the evidence and produce closed observations; deterministic rules control escrow authorization.

## Current status

**Pre-deployment engineering build. Not a production-ready water-safety or payment service.**

- Contract and local test suite implemented.
- English-only frontend with supplied logo, local proof preparation, guarded wallet workflows and persistent transaction reconciliation.
- Contract address intentionally empty. Live writes disabled until deployment, source parity and live audit are verified.
- Public-source negative/ambiguous fixtures found and HTTP/hash checked. A repository-owned synthetic positive triplet is included and explicitly labeled; it is not a real-world service record.
- No deployment or on-chain test was performed for this project.

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
