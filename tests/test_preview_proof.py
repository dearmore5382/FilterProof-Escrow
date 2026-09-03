import json
from unittest.mock import patch
import pytest
from gltest.direct import wasi_mock
from test_contract_direct import (deploy, sync, manifest, mock_bundle, vision,
                                  address_text, create_funded, run_validator)


def preview_args(contract, technician, digest):
    return ["https://proof.example/job-0.json", digest, 0, "BKK-HOTEL-07",
            "RO-SKID-991", address_text(contract, technician), "SED-5M, CARBON-10, RO-4040"]


def test_positive_preview_never_creates_job_or_authorizes_payment():
    vm, contract, _, technician, _ = deploy()
    body, digest = manifest(contract, technician)
    mock_bundle(vm, body, vision())
    with vm.activate():
        sync(vm, contract)
        result = json.loads(contract.preview_proof(*preview_args(contract, technician, digest)))
        assert result["scope"] == "PREVIEW_ONLY_NO_PAYMENT_AUTHORIZATION"
        assert result["outcome"] == {"verdict":"SERVICE_CONFIRMED", "reason":"ALL_CHECKS_CONFIRMED"}
        assert contract.get_counts() == "0|0" and contract.get_job(0) == "NOT_FOUND"
        assert contract.execute_release(0) == "JOB_NOT_FOUND"
        assert run_validator(vm, contract)


def test_positive_preview_cannot_unlock_or_mutate_funded_job():
    vm, contract, _, technician, outsider = deploy()
    create_funded(vm, contract, technician)
    body, digest = manifest(contract, technician)
    mock_bundle(vm, body, vision())
    with vm.activate():
        before = (contract.get_counts(), contract.get_job(0), contract.get_accounting(0))
        with vm.prank(outsider):
            sync(vm, contract)
            assert json.loads(contract.preview_proof(*preview_args(contract, technician, digest)))["outcome"]["verdict"] == "SERVICE_CONFIRMED"
            assert contract.execute_release(0) == "RELEASE_NOT_AUTHORIZED"
            assert contract.execute_refund(0) == "REFUND_NOT_AUTHORIZED"
        assert (contract.get_counts(), contract.get_job(0), contract.get_accounting(0)) == before


@pytest.mark.parametrize("index,value,error", [
    (0,"http://proof.example/x","INVALID_MANIFEST_URL"),
    (1,"a"*63,"INVALID_MANIFEST_HASH"),
    (3,"","INVALID_SITE"), (4,"","INVALID_SERIAL"),
    (5,"0x"+"0"*40,"INVALID_TECHNICIAN"), (6,"","INVALID_FILTERS"),
])
def test_invalid_preview_rejected_before_model(index, value, error):
    vm, contract, _, technician, _ = deploy()
    args = preview_args(contract, technician, "a"*64)
    args[index] = value
    gl = contract._instance.preview_proof.__globals__["gl"]
    with vm.activate(), patch.object(gl.vm, "run_nondet_unsafe") as nondet:
        sync(vm, contract)
        with pytest.raises(Exception, match=error): contract.preview_proof(*args)
        nondet.assert_not_called()
        assert contract.get_counts() == "0|0"


def test_nonzero_preview_rejected_before_nondeterminism():
    vm, contract, _, technician, _ = deploy()
    gl = contract._instance.preview_proof.__globals__["gl"]
    with vm.activate(), patch.object(gl.vm, "run_nondet_unsafe") as nondet:
        vm.value = 1
        sync(vm, contract)
        with pytest.raises(Exception): contract.preview_proof(*preview_args(contract, technician, "a"*64))
        nondet.assert_not_called()


def test_binding_failure_then_preview_recovery_without_attempt_consumption():
    vm, contract, _, technician, _ = deploy()
    body, digest = manifest(contract, technician)
    mock_bundle(vm, body, vision())
    with vm.activate():
        sync(vm, contract)
        with patch.object(wasi_mock, "_handle_llm_request") as model:
            result = json.loads(contract.preview_proof(*preview_args(contract, technician, "0"*64)))
            assert result["outcome"]["reason"] == "MANIFEST_BINDING_MISMATCH"
            model.assert_not_called()
        assert json.loads(contract.preview_proof(*preview_args(contract, technician, digest)))["outcome"]["verdict"] == "SERVICE_CONFIRMED"
        assert contract.get_counts() == "0|0"


def test_preview_technical_error_propagates_without_mutation():
    vm, contract, _, technician, _ = deploy()
    body, digest = manifest(contract, technician)
    mock_bundle(vm, body, vision())
    with vm.activate(), patch.object(wasi_mock,"_handle_llm_request",return_value={"error":"controlled failure"}):
        sync(vm, contract)
        with pytest.raises(Exception, match="OVERVIEW_MODEL_CALL_ERROR"):
            contract.preview_proof(*preview_args(contract, technician, digest))
        assert contract.get_counts() == "0|0"


def test_preview_validator_rejects_independent_negative():
    vm, contract, _, technician, _ = deploy()
    body, digest = manifest(contract, technician)
    mock_bundle(vm, body, vision())
    with vm.activate():
        sync(vm, contract)
        contract.preview_proof(*preview_args(contract, technician, digest))
        mock_bundle(vm, body, vision(asset_identity="MISMATCH"))
        assert not run_validator(vm, contract)
        assert contract.get_counts() == "0|0"
