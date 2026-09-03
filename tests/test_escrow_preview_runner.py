import base64
import hashlib
import json
import pytest
from genlayer_py.abi import calldata
from diagnostics.run_escrow_preview import (case_arguments, validate_receipt, ROOT,
                                           SOURCE_SHA256, MANIFEST_SHA256)


def receipt(parsed):
    return {"execution_result":"SUCCESS","result":base64.b64encode(b'\x00'+calldata.encode(json.dumps(parsed))).decode()}


def test_locked_source_manifest_and_case_inputs():
    assert hashlib.sha256((ROOT / "contracts/FilterProofEscrow.py").read_bytes()).hexdigest() == SOURCE_SHA256
    assert hashlib.sha256((ROOT / "fixtures/synthetic-happy/manifest.json").read_bytes()).hexdigest() == MANIFEST_SHA256
    good = case_arguments("positive")
    for case, index in (("wrong-manifest-hash",1),("cross-job",2),("invalid-url",0)):
        changed = case_arguments(case)
        assert changed[index] != good[index]
        assert all(a == b for i,(a,b) in enumerate(zip(good,changed)) if i != index)


def test_expected_success_requires_exact_observations_and_scope():
    parsed = {"scope":"PREVIEW_ONLY_NO_PAYMENT_AUTHORIZATION",
              "outcome":{"verdict":"SERVICE_CONFIRMED","reason":"ALL_CHECKS_CONFIRMED"},
              "observation":{"binding_status":"MATCH","asset_identity":"MATCH","filter_replacement":"COMPLETE",
                             "before_after_continuity":"CONSISTENT","pressure_evidence":"PLAUSIBLE","tamper_signal":"NONE"}}
    validate_receipt("positive",receipt(parsed))
    parsed["observation"]["asset_identity"] = "UNCERTAIN"
    with pytest.raises(RuntimeError,match="OBSERVATIONS_MISMATCH"):
        validate_receipt("positive",receipt(parsed))


def test_expected_input_failure_is_not_generic_success():
    error = {"execution_result":"ERROR","result":base64.b64encode(b'\x01INVALID_MANIFEST_URL').decode()}
    validate_receipt("invalid-url",error)
    with pytest.raises(RuntimeError): validate_receipt("positive",error)
    error["execution_result"] = "SUCCESS"
    with pytest.raises(RuntimeError): validate_receipt("invalid-url",error)
