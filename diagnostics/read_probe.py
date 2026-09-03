"""Unsigned, read-only source check and one snapshot simulation per invocation."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import requests
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "0x9D1F3F657530C83500669ddBFa65568F6A185c18"
SENDER = "0x736A168247e3f0C52F7907c9a8fDac572DF9c8bB"
RPC = "https://studio.genlayer.com/api"


def redact(value):
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()
                if key not in {"node_config", "contract_state", "private_key", "api_key", "secret", "token"}}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def rpc(method, params):
    if method not in {"gen_getContractCode", "gen_call", "sim_call", "gen_getContractSchema"}:
        raise ValueError("Read-only methods only")
    response = requests.post(RPC, json={"jsonrpc":"2.0", "id":1, "method":method, "params":params}, timeout=55)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        error = redact(data["error"])
        receipt = error.get("data", {}).get("receipt")
        if method == "sim_call" and isinstance(receipt, dict):
            receipt["rpc_error"] = {"code":error.get("code"), "message":error.get("message")}
            return receipt
        raise RuntimeError(json.dumps(error))
    return redact(data["result"])


def params(kind, method, args):
    return {"type":kind, "to":ADDRESS, "from":SENDER, "value":"0x0",
            "data":serialize([calldata.encode({"method":method,"args":args}), b'\x00'])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=("preflight","control","fetch","text","json","one-text","one-json","two-text","two-json","detail-json"))
    case = parser.parse_args().case
    deployed = base64.b64decode(rpc("gen_getContractCode", [ADDRESS]))
    source = (ROOT / "diagnostics/FilterProofVisionProbe.py").read_bytes()
    if deployed != source:
        raise RuntimeError("Exact deployed source mismatch: " + hashlib.sha256(deployed).hexdigest())
    encoded = rpc("gen_call", [params("read", "info", [])])
    info = calldata.decode(bytes.fromhex(encoded.removeprefix('0x')))
    if info != "FilterProofVisionProbe-v1|DIAGNOSTIC_ONLY|NO_SERVICE_VERDICT|SEND_ZERO_VALUE":
        raise RuntimeError("Probe identity mismatch")
    print(json.dumps({"contract":ADDRESS,"exact_source_sha256":hashlib.sha256(deployed).hexdigest(),"info":info}), flush=True)
    if case == "preflight":
        print(json.dumps(rpc("gen_getContractSchema", [ADDRESS])))
        return
    receipt = rpc("sim_call", [params("write", "run", [case])])
    folder = ROOT / ".diagnostic-private"
    folder.mkdir(exist_ok=True)
    (folder / ("probe-simulation-" + case + ".json")).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("SIMULATION_ONLY_NO_TRANSACTION", case)
    print("receipt_keys", list(receipt))
    for key in ("execution_result", "result", "genvm_result", "eq_outputs"):
        if key in receipt:
            print(key, json.dumps(receipt[key])[:18000])
    if receipt.get("execution_result") != "SUCCESS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
