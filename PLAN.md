# FilterProof Escrow — build plan

## Product

A focused DApp for one commercial-water-filtration service: replacing a declared set of filter cartridges on one identified system. A site operator escrows GEN for an assigned technician. The technician submits an immutable proof manifest containing before, after, serial/gauge images and structured service measurements. GenLayer validators inspect the same bytes and images independently.

This product does not certify drinking-water safety, regulatory compliance, laboratory water quality, technician licensing, image capture time, physical location, or authenticity beyond visible evidence and sealed manifest bindings.

## Delivery stages

1. Lock actors, evidence schema, state machine, precedence, and threat model.
2. Implement deterministic manifest validation, image assessment, and escrow accounting.
3. Build pure derivation, static, Direct Mode, differential-consensus, and adversarial tests.
4. Run P1/P2 audit and fix every reproducible issue before deployment.
5. Build a responsive wallet DApp using the supplied logo and a fail-closed transaction journal.
6. Run frontend unit checks, lint-like static checks, and production build.
7. Freeze contract source hash and deployment/audit runbook.
8. Stop and ask the user to deploy the exact frozen contract.
9. After deployment only: verify source parity, run the on-chain audit, wire the verified address, rebuild, and test transaction reconciliation.

## Adversarial audit model

### Happy path

- Operator creates and funds a work order.
- Assigned technician submits a hash-bound manifest.
- Independent image observations confirm identity, replacement, continuity, pressure plausibility, and no visible tamper signal.
- Permissionless settlement pays the technician once.

### Failure paths

- Wrong operator, wrong technician, wrong value, invalid URL/hash/address/timestamp.
- Submission before funding, assessment before proof, settlement before authorization.
- Manifest unavailable, oversized, malformed, wrong schema/job/actor/asset/site, digest mismatch, or image fetch failure.
- Malformed/oversized model output and validator disagreement.
- Expiry recovery, second failed attempt refund, replayed assessment/settlement, and immutable history.

### Adversarial combinations

- Correct serial with wrong site or wrong filter set.
- Changed numeric reading plus uncertain image.
- Same before/after image with plausible text claims.
- Prompt injection in notes or image text.
- Reused manifest across jobs.
- Mismatch and uncertainty together; substantive negative must win.
- First failed proof followed by stale/replayed proof, then a valid correction.
- Two simultaneous-looking settlement attempts; only the first authorized state can mutate accounting.

## Deployment stop condition

No deploy command is part of this build. The user is notified only after all local gates pass and the exact source SHA-256 is frozen.
