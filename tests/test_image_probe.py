import ast
import hashlib
import json
from unittest.mock import patch
import pytest
from gltest.direct import wasi_mock
from test_vision_probe import ROOT, setup_probe

SOURCE = ROOT / "diagnostics/FilterProofImageProbe.py"
MANIFEST = json.loads((ROOT / "fixtures/synthetic-happy/manifest-png.json").read_text())
PREFIXES = ("before", "after", "serial_gauge")
URLS = [MANIFEST[p + "_image_url"] for p in PREFIXES]
HASHES = [MANIFEST[p + "_image_sha256"] for p in PREFIXES]
BODIES = [(ROOT / "fixtures/synthetic-happy" / f).read_bytes() for f in ("before.png", "after.png", "serial-gauge.png")]


@pytest.fixture(autouse=True, params=["FilterProofImageProbe.py", "FilterProofImageProbeV3.py"])
def probe_revision(request, monkeypatch):
    monkeypatch.setitem(globals(), "SOURCE", ROOT / "diagnostics" / request.param)


def setup():
    vm, contract, ns = setup_probe(SOURCE)
    for url, body in zip(URLS, BODIES):
        vm.mock_web(url, {"status":200, "body":body})
    return vm, contract, ns


def test_reusable_surface_preserves_runner_and_never_holds_funds():
    text = SOURCE.read_text()
    cls = next(n for n in ast.parse(text).body if isinstance(n, ast.ClassDef))
    assert [n.name for n in cls.body if isinstance(n, ast.FunctionDef)] == ["__init__", "info", "run"]
    assert not any(isinstance(n, ast.AnnAssign) for n in cls.body)
    assert "payable" not in text and "emit_transfer" not in text
    assert text.splitlines()[:2] == (ROOT / "contracts/FilterProofEscrow.py").read_text().splitlines()[:2]
    for body, digest in zip(BODIES, HASHES):
        assert hashlib.sha256(body).hexdigest() == digest


@pytest.mark.parametrize("mode,indices", [
    ("control", []), ("fetch", [0,1,2]), ("fetch", [2]),
    ("text", []), ("json", []), ("text", [0]), ("json", [0]),
    ("text", [0,1]), ("json", [0,1]), ("json", [1,2]),
])
def test_each_mode_and_pair_exact_sdk_payload(mode, indices):
    vm, contract, _ = setup()
    urls, hashes = [URLS[i] for i in indices], [HASHES[i] for i in indices]
    calls = []
    original = wasi_mock._handle_llm_request
    def capture(context, payload):
        calls.append(payload)
        return original(context, payload)
    with vm.activate(), patch.object(wasi_mock, "_handle_llm_request", side_effect=capture):
        result = contract.run(mode, urls, hashes)
    if mode == "control":
        assert result == "CONTROL_OK" and calls == []
    else:
        parsed = json.loads(result)
        assert parsed["images"] == len(indices)
        assert parsed["binding"] == hashlib.sha256(json.dumps([mode,urls,hashes],separators=(",",":")).encode()).hexdigest()
        if mode == "fetch":
            assert parsed["status"] == "FETCH_VERIFIED" and calls == []
        else:
            assert parsed["status"] == "MODEL_ROUNDTRIP" and len(calls) == 1
            assert calls[0]["response_format"] == mode
            assert calls[0]["images"] == [BODIES[i] for i in indices]


@pytest.mark.parametrize("mode,urls,hashes,code", [
    ("bogus", [], [], "UNKNOWN_MODE"),
    ("control", URLS[:1], HASHES[:1], "IMAGE_COUNT"),
    ("fetch", [], [], "IMAGE_COUNT"),
    ("json", URLS, HASHES, "IMAGE_COUNT"),
    ("json", URLS[:1], [], "URL_HASH_COUNT"),
    ("json", [URLS[0]]*2, HASHES[:2], "DUPLICATE_IMAGE"),
    ("json", URLS[:2], [HASHES[0]]*2, "DUPLICATE_IMAGE"),
    ("json", URLS[:1], ["A"*64], "INVALID_SHA256"),
    ("json", URLS[:1], ["a"*63], "INVALID_SHA256"),
])
def test_guards_precede_nondeterminism(mode, urls, hashes, code):
    vm, contract, ns = setup()
    with vm.activate(), patch.object(ns["gl"].vm, "run_nondet_unsafe") as nondet:
        with pytest.raises(Exception, match="PROBE_" + code):
            contract.run(mode, urls, hashes)
        nondet.assert_not_called()


@pytest.mark.parametrize("url", [
    "http://raw.githubusercontent.com/u/r/" + "a"*40 + "/x.png",
    "https://127.0.0.1/x.png", "https://localhost/x.png",
    "https://raw.githubusercontent.com.evil.example/u/r/x.png",
    "https://raw.githubusercontent.com:443/u/r/x.png",
    "https://user@raw.githubusercontent.com/u/r/x.png",
    "https://raw.githubusercontent.com/u/r/main/x.png",
    URLS[0] + "?raw=1", URLS[0] + "#x", URLS[0] + "\n",
    URLS[0] + "/../x", URLS[0] + "%00", "https://gateway.pinata.cloud/ipfs/short",
])
def test_unsafe_or_mutable_urls_rejected(url):
    vm, contract, ns = setup()
    with vm.activate(), patch.object(ns["gl"].vm, "run_nondet_unsafe") as nondet:
        with pytest.raises(Exception, match="PROBE_PUBLIC_PINNED_URL_REQUIRED"):
            contract.run("json", [url], HASHES[:1])
        nondet.assert_not_called()


@pytest.mark.parametrize("kind,code", [
    ("http", "PROBE_HTTP_503"), ("hash", "PROBE_IMAGE_HASH_0"),
    ("empty", "PROBE_IMAGE_SIZE"), ("oversize", "PROBE_IMAGE_SIZE"),
    ("webp", "PROBE_UNSUPPORTED_FORMAT_USE_PNG"),
])
def test_fetch_errors_never_reach_model(kind, code):
    vm, contract, _ = setup()
    body = BODIES[0]
    if kind == "empty": body = b""
    elif kind == "oversize": body = b"x" * 4_000_001
    elif kind == "webp": body = (ROOT / "fixtures/synthetic-happy/before-v2.webp").read_bytes()
    vm.clear_mocks()
    vm.mock_web(URLS[0], {"status":503 if kind == "http" else 200, "body":body})
    digest = "0"*64 if kind == "hash" else hashlib.sha256(body).hexdigest()
    with vm.activate(), patch.object(wasi_mock, "_handle_llm_request") as model:
        with pytest.raises(Exception, match=code):
            contract.run("json", URLS[:1], [digest])
        model.assert_not_called()


@pytest.mark.parametrize("response,error", [
    ({"error":"CONTROLLED_RUNTIME_ERROR"}, "CONTROLLED_RUNTIME_ERROR"),
    ({"ok":"not-json"}, "Expecting value"),
    ({"ok":{}}, "PROBE_OUTPUT_SCHEMA"),
    ({"ok": {"marker":"PAY", "visible":"NO_IMAGES"}}, "PROBE_OUTPUT_FIELDS"),
    ({"ok":"x"*2001}, "PROBE_OUTPUT_SIZE"),
])
def test_runtime_and_parse_failures_keep_real_exception(response, error, capsys):
    vm, contract, _ = setup()
    with vm.activate(), patch.object(wasi_mock, "_handle_llm_request", return_value=response):
        with pytest.raises(Exception, match=error):
            contract.run("json", [], [])
    assert "EXEC_PROMPT" in capsys.readouterr().out


def test_different_inputs_are_bound_and_validator_checks_independently():
    vm, contract, ns = setup()
    with vm.activate():
        first = json.loads(contract.run("json", URLS[:1], HASHES[:1]))
        second = json.loads(contract.run("json", URLS[1:2], HASHES[1:2]))
        assert first["binding"] != second["binding"]
        stored, _, validator = vm._captured_validators[-1]
        vm._in_nondet = True
        try:
            assert validator(ns["gl"].vm.Return(calldata=dict(stored, visible="another description")))
            assert not validator(ns["gl"].vm.Return(calldata=first))
            assert not validator(ns["gl"].vm.Return(calldata=dict(stored, images=True)))
            vm.clear_mocks()
            vm.mock_web(URLS[1], {"status":200, "body":b"changed"})
            assert not validator(ns["gl"].vm.Return(calldata=stored))
        finally:
            vm._in_nondet = False


def test_reject_attached_value_before_nondeterminism():
    vm, contract, ns = setup()
    proxy = ns["gl"]
    proxy._cached_gl.message = proxy.message._replace(value=type(proxy.message.value)(1))
    with vm.activate(), patch.object(proxy.vm, "run_nondet_unsafe") as nondet:
        with pytest.raises(Exception):
            contract.run("control", [], [])
        nondet.assert_not_called()
