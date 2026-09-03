# Constructor snapshot diagnostic — not a semantic assessment

One unsigned control was run at `2026-09-03T08:16:39.684230+00:00` using the
known stateless v3 probe as snapshot anchor:
`0x9Bed86f3ccf45b778c09e33A91aD14e5C65c3857`.
The source is `diagnostics/SnapshotControl.py` (no model/fetch); runner is
`diagnostics/simulate_source.py`. Request supplies explicit UTC in sim_config.

Observed result: execution ERROR, `exit_code 1`. Trace reached
`_genlayer_runner.py -> root_slot.lock_default -> storage_write`, then
`SystemError: 6: forbidden`. No control marker was printed. Thus this path
did not execute the user constructor; it cannot evaluate semantic fixtures.
The existing probe source hash and info matched before and after. No on-chain
deployment, signing, broadcast or value transfer occurred. No retry was made.

The public [Studio endpoint](https://github.com/genlayerlabs/genlayer-studio/blob/main/backend/protocol_rpc/endpoints.py)
passes `sim_config.genvm_datetime` to constructor execution. The public
[node implementation](https://github.com/genlayerlabs/genlayer-studio/blob/main/backend/node/base.py)
uses a naive current datetime when omitted and later asserts timezone presence.
This suggests a cause for earlier empty constructor errors, not an attestation
of the hosted server build. With explicit UTC, the observed failure is now
storage-related. Re-initializing an already initialized snapshot is a plausible
explanation, not permission to bypass frozen-storage checks.

Chosen supported path: a user-deployed escrow with a non-persisting preview
method, evaluated by existing-contract write simulations already proven to
work. No admin changes, storage unlocking or provider configuration changes.
