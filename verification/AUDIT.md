# Adversarial audit — remediation required

This is an engineering self-review, not an independent security certification.

## Verified so far

- 37 pytest tests pass, including happy-path authorization/payout, failures, independent captured-validator checks, stateful adversarial combinations and synthetic-fixture integrity. One test enumerates all 729 closed-observation combinations.
- GenVM lint, semantic validation and SDK typecheck pass for the current source.
- The first Studionet deployment at `0x404c3A6d50B04B93b8e4F8a9f7c394CE21adeeBA` was exercised and safely refunded. It must not be presented as the final deployment.

## Findings and changes

| Finding | Change | Evidence |
| --- | --- | --- |
| Manifest hash did not bind fetched image bytes | Require three distinct SHA-256 image commitments and verify fetched bytes | image substitution regression test |
| Calendar-shaped but impossible recovery dates accepted | Validate calendar days, leap years and clock bounds | calendar regression test |
| Expired drafts could still receive funding | Revert funding at/after recovery deadline | expired funding regression test |
| HTTP error responses could be parsed as evidence | Require SDK response `status == 200` | transport test |
| IPv4 literal host bypassed URL policy | Reject numeric hosts | pure URL test |
| Malformed model output was conflated with missing transport | Preserve verified binding and mark visual uncertainty | malformed-model test |
| Test fixtures used reserved delimiter | Replace filter list delimiter with commas | happy path |
| Repeated HTTP mocks retained the first response | Clear registered mocks between scenarios | correction sequence |
| AI could supply the code-owned binding key before overwrite | Require exactly the five model-owned fields before inserting binding status | malformed/extra-field tests |
| Numeric pressure coercion accepted booleans/fractions | Require exact integer types | frontend coercion cases; contract input validation |
| Wallet interruption could lose the transaction hash | Persist a pre-signing intent, retain uncertainty and expose hash recovery | implementation reviewed; browser E2E still open |
| Separate tabs could independently submit | Web Locks plus persistent intent and fresh journal read before signing | implementation reviewed; browser E2E still open |
| Source images could be merged into a false service claim | Public gallery fixture explicitly classified as insufficient identity | public source registry; no happy-path claim |
| Vision call sent three images although the active validator interface supports at most two | Continue fetching and hash-verifying all three; send only the complete BEFORE and AFTER overviews to vision | two finalized attempts returned `binding_status=MATCH` but visual fallback; assessment transactions recorded below |
| Legacy SDK sends structured-output mode as protocol `json`; the active runtime expects the newer `json2` transform, and the call ended before `EXEC_PROMPT` | Keep the validated legacy runner but request text output; parse and enforce the same exact closed JSON schema in contract code | second deployment receipt had no `EXEC_PROMPT` host call; latest SDK source maps public `response_format="json"` to internal `json2` |

## Honest limits / remaining gates

- Direct Mode mocks HTTP and AI. It does not establish real-image accuracy, prompt-injection resistance of a live model, validator consensus, or final on-chain transfers.
- Direct Mode `emit_transfer` assertions establish authorization/accounting only; emitted transfer execution and actual recipient balances need on-chain evidence.
- URL syntax policy is not a DNS/private-network security boundary. DNS/redirect handling depends on the GenLayer web provider.
- Hashes prove byte identity, not that photos depict a real service, capture date or site. Images can be staged or generated.
- AI cannot certify water safety, sanitary compliance, flow quality or lab results.
- Frontend transaction/evidence logic has ten passing unit tests, application-source lint and full typechecking; production builds pass. Differential validator tests, an exact-byte-verified public synthetic fixture and the live runbook are present. Real wallet/browser integration and live visual/model checks remain post-deployment gates.
- Runtime reproducibility: Direct Mode is pinned to archive `v0.3.0-rc7`, but loads and asserts the exact `py-lib-genlayer-std:11rhn002yfajawsz7fai6mykznbxkxs6l91iskj5cm82c92qhy3v` required by the contract's pinned runner. The local `v0.2.16` extraction is incomplete and fails import; both archives' runner manifests point to the same SDK hash. No silent latest-SDK substitution is used.
- Lint scope excludes the unmodified scaffold component catalog, which has upstream lint warnings; full TypeScript checking includes it.
- Optional WebMCP tool is implemented but not runtime-verified in a supporting browser.

## Required post-deployment audit

Use fresh testnet-only wallets. Record every transaction hash, method, expected outcome, actual finalized receipt, job/attempt readback, and balance effect. Separate happy paths, failure paths, and multi-transaction adversarial combinations. Do not count business rejection strings as successful workflow operations merely because execution was successful.

If a submitted transaction remains nonterminal, continue checking the same hash; never resubmit automatically. Stop when configuration or source parity is wrong. Never describe a pending transaction as passed.

## First deployment outcome

- Attempt 1 assessment `0x49da067341915a9addbd541902f859d050f944447cb5dd5734d556b1fc79ad35`: binding matched; visual observation fell back to all `UNCERTAIN`; `CORRECTION_REQUIRED`.
- Attempt 2 assessment `0xdc30257c36b96440448e56f394de575716394f8eaee1370a723bd3179ce7dba2`: binding matched; visual observation again fell back to all `UNCERTAIN`; `REFUND_AUTHORIZED`.
- Refund `0x303e7f1390015c702e08ad9493d462c82124476371f517b8d45bda35aee08995` finalized with majority agreement; emitted child transfer `0x49bdcdd35e7f6a154ccaed5d03235509353bc060b3728e13b33b8e72cf4e1f48`.
- Final accounting: bounty `100000000000000000`, held `0`, paid `0`, refunded `100000000000000000`, contract balance `0`.
- This is a successful fail-closed/custody test, not a successful happy path.

## Second deployment outcome

- Deployment `0x3512b8E2343A59c1AC5314F6d52c4fd0F26079c2` used only two vision images, but its first assessment `0xd1900e60b97e0b897727bd8db42ae3dc57092cd4ebf30c9d6fb4216d20e5dee6` still returned the safe visual fallback before any `EXEC_PROMPT` host call.
- The second attempt deliberately supplied a wrong manifest digest to test binding failure. Assessment `0xc2973bf728b6e0b3a356aa1bd08bda96d25436ed27d2d4b9e8c48478c291be84` returned `MANIFEST_BINDING_MISMATCH` and authorized refund.
- Refund `0x31438d620955510018479b2a4ffc8078dcaa6d3639d5dd021edbed53c24e52bd` finalized with majority agreement; emitted child transfer `0x21e8f61a3a0dc4215100a3d54f84d19f7dbe3bea22ec94bb12e3c9e54a6f6332`.
- Operator balance increased by exactly `100000000000000000`; final contract accounting and balance are zero-held/zero-paid/full-refunded/zero-balance.
- This deployment is superseded and must not be configured in the frontend.
