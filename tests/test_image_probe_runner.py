import json
from unittest.mock import patch
from genlayer_py.abi import calldata
from diagnostics.run_image_probe import arguments, call_params, decode_result, decode_error, CASES
from diagnostics.read_probe import redact, rpc


def test_case_mapping_keeps_overview_and_detail_order():
    fixture = {prefix+suffix:prefix+suffix for prefix in ("before","after","serial_gauge")
               for suffix in ("_image_url","_image_sha256")}
    assert arguments("control",fixture) == ["control",[],[]]
    assert arguments("detail-json",fixture) == ["json",["after_image_url","serial_gauge_image_url"],
                                                ["after_image_sha256","serial_gauge_image_sha256"]]
    for case in CASES:
        mode, urls, hashes = arguments(case,fixture)
        assert len(urls) == len(hashes) <= (3 if mode == "fetch" else 2)


def test_call_is_zero_value_and_never_broadcasts():
    value = call_params("0x"+"1"*40,"write","run",["control",[],[]])
    assert value["value"] == "0x0" and value["type"] == "write"
    with patch("diagnostics.read_probe.requests.post") as post:
        try:
            rpc("eth_sendRawTransaction",[])
        except ValueError:
            pass
        else:
            raise AssertionError("Signing/broadcast method was not rejected")
        post.assert_not_called()


def test_sensitive_node_config_removed_and_return_decoding():
    import base64
    payload = {"node_config":{"private_key":"DO_NOT_EXPORT"},"nested":{"api_key":"DO_NOT_EXPORT"},"result":"ok"}
    assert "DO_NOT_EXPORT" not in json.dumps(redact(payload))
    encoded = base64.b64encode(b'\x00'+calldata.encode("CONTROL_OK")).decode()
    assert decode_result({"result":encoded}) == "CONTROL_OK"
    assert decode_result({"result":base64.b64encode(b'\x02error').decode()}) is None
    assert decode_error({"result":encoded}) is None
    assert decode_error({"result":base64.b64encode(b'\x01PROBE_OUTPUT_VISIBLE').decode()}) == "PROBE_OUTPUT_VISIBLE"
