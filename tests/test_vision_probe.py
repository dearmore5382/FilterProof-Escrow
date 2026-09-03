import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest
from gltest.direct import VMContext, create_address, deploy_contract, wasi_mock

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "diagnostics/FilterProofVisionProbe.py"


def setup_probe(source=SOURCE):
    vm = VMContext(create_address("diagnostic-operator"))
    with patch("os.unlink", lambda _path: None), vm.activate():
        contract = deploy_contract(source, vm, sdk_version="v0.3.0-rc7")
        proxy = contract._instance.run.__globals__["gl"]
        _ = proxy.nondet
    sdk_root = str(Path(proxy._cached_gl.__file__).resolve().parents[2])
    assert Path(sdk_root).name == "11rhn002yfajawsz7fai6mykznbxkxs6l91iskj5cm82c92qhy3v"
    if sdk_root not in sys.path:
        sys.path.insert(0, sdk_root)
    importlib.import_module("genlayer")
    namespace = contract._instance.run.__globals__
    for filename in namespace.get("FILES", ()):
        body = (ROOT / "fixtures/synthetic-happy" / filename).read_bytes()
        vm.mock_web(namespace["BASE"] + filename, {"status": 200, "body": body})
    vm.mock_llm("Return only JSON", '{"marker":"FILTERPROOF_PROBE_OK","visible":"NO_IMAGES"}')
    return vm, contract, namespace


def test_probe_surface_no_custody_and_same_pinned_fixtures():
    source = SOURCE.read_text()
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    assert [n.name for n in cls.body if isinstance(n, ast.FunctionDef)] == ["__init__", "info", "run"]
    assert "payable" not in "\n".join(ast.unparse(n) for n in cls.body)
    assert not any(isinstance(n, ast.AnnAssign) for n in cls.body)
    assert "emit_transfer" not in source
    assert source.splitlines()[:2] == (ROOT / "contracts/FilterProofEscrow.py").read_text().splitlines()[:2]
    _, _, ns = setup_probe()
    manifest = json.loads((ROOT / "fixtures/synthetic-happy/manifest-v2.json").read_text())
    for i, prefix in enumerate(("before", "after", "serial_gauge")):
        assert ns["BASE"] + ns["FILES"][i] == manifest[prefix + "_image_url"]
        assert ns["DIGESTS"][i] == manifest[prefix + "_image_sha256"]


@pytest.mark.parametrize("case,count,format_name", [
    ("control", 0, None), ("fetch", 0, None),
    ("text", 0, "text"), ("json", 0, "json"),
    ("one-text", 1, "text"), ("one-json", 1, "json"),
    ("two-text", 2, "text"), ("two-json", 2, "json"),
    ("detail-json", 2, "json"),
])
def test_probe_each_mode_uses_expected_sdk_boundary(case, count, format_name):
    vm, contract, ns = setup_probe()
    calls = []
    original = wasi_mock._handle_llm_request

    def capture(context, payload):
        calls.append(payload)
        return original(context, payload)

    with vm.activate(), patch.object(wasi_mock, "_handle_llm_request", side_effect=capture):
        result = contract.run(case)
    if case == "control":
        assert result == "CONTROL_OK" and not calls
    elif case == "fetch":
        assert json.loads(result)["status"] == "FETCH_VERIFIED" and not calls
    else:
        assert json.loads(result)["status"] == "MODEL_ROUNDTRIP"
        assert len(calls) == 1 and len(calls[0]["images"]) == count
        assert calls[0]["response_format"] == format_name
        expected = [1, 2] if case == "detail-json" else list(range(count))
        assert [hashlib.sha256(b).hexdigest() for b in calls[0]["images"]] == [ns["DIGESTS"][i] for i in expected]


@pytest.mark.parametrize("bad", ["bogus", "two-json ", "", "three-json"])
def test_unknown_case_never_calls_model(bad):
    vm, contract, _ = setup_probe()
    with vm.activate(), patch.object(wasi_mock, "_handle_llm_request") as model:
        with pytest.raises(Exception, match="PROBE_UNKNOWN_CASE"):
            contract.run(bad)
        model.assert_not_called()


def test_probe_rejects_value():
    vm, contract, ns = setup_probe()
    with vm.activate():
        vm.value = 1
        proxy = ns["gl"]
        proxy._cached_gl.message = proxy.message._replace(value=type(proxy.message.value)(1))
        with pytest.raises(Exception):
            contract.run("control")


@pytest.mark.parametrize("response,error", [
    ({"error": "CONTROLLED_PROVIDER_FAILURE"}, "CONTROLLED_PROVIDER_FAILURE"),
    ({"ok": "not-json"}, "Expecting value"),
    ({"ok": {}}, "PROBE_OUTPUT_SCHEMA"),
    ({"ok": '{"marker":"PAY","visible":"NO_IMAGES"}'}, "PROBE_OUTPUT_FIELDS"),
])
def test_errors_are_not_swallowed(response, error, capsys):
    vm, contract, _ = setup_probe()
    with vm.activate(), patch.object(wasi_mock, "_handle_llm_request", return_value=response):
        with pytest.raises(Exception, match=error):
            contract.run("json")
    output = capsys.readouterr().out
    assert "EXEC_PROMPT" in output
    assert "COMPLETE" not in output


def test_bad_image_stops_before_model():
    vm, contract, ns = setup_probe()
    vm.clear_mocks()
    vm.mock_web(ns["BASE"] + ns["FILES"][0], {"status": 200, "body": b"substituted"})
    with vm.activate(), patch.object(wasi_mock, "_handle_llm_request") as model:
        with pytest.raises(Exception, match="PROBE_IMAGE_HASH_0"):
            contract.run("one-json")
        model.assert_not_called()


def test_independent_validator_checks_roundtrip_not_description():
    vm, contract, ns = setup_probe()
    with vm.activate():
        contract.run("one-json")
        stored, _, validator = vm._captured_validators[-1]
        vm._in_nondet = True
        try:
            alternative = dict(stored, visible="Another harmless description")
            assert validator(ns["gl"].vm.Return(calldata=alternative)) is True
            assert validator(ns["gl"].vm.Return(calldata=dict(stored, images=99))) is False
            with patch.object(wasi_mock, "_handle_llm_request", return_value={"error": "validator unavailable"}):
                assert validator(ns["gl"].vm.Return(calldata=stored)) is False
        finally:
            vm._in_nondet = False
