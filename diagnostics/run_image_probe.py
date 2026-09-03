"""One unsigned simulation on an explicitly supplied versioned probe; never deploys."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from diagnostics.read_probe import rpc, SENDER

ROOT = Path(__file__).resolve().parents[1]
INFO = "FilterProofImageProbe-v2|URL_SHA256_INPUTS|DIAGNOSTIC_ONLY|SEND_ZERO_VALUE"
SOURCES = {"v2":"FilterProofImageProbe.py", "v3":"FilterProofImageProbeV3.py"}
CASES = {"control":("control",()), "fetch":("fetch",(0,1,2)),
         "text":("text",()), "json":("json",()),
         "one-text":("text",(0,)), "one-json":("json",(0,)),
         "two-text":("text",(0,1)), "two-json":("json",(0,1)),
         "detail-json":("json",(1,2))}


def arguments(case, fixture):
    mode, indices = CASES[case]
    prefixes = ("before", "after", "serial_gauge")
    return [mode, [fixture[prefixes[i]+"_image_url"] for i in indices],
            [fixture[prefixes[i]+"_image_sha256"] for i in indices]]


def call_params(address, kind, method, args):
    return {"type":kind, "to":address, "from":SENDER, "value":"0x0",
            "data":serialize([calldata.encode({"method":method,"args":args}), b'\x00'])}


def decode_result(receipt):
    raw = base64.b64decode(receipt["result"])
    if not raw or raw[0] != 0:
        return None
    return calldata.decode(raw[1:])


def decode_error(receipt):
    raw = base64.b64decode(receipt["result"])
    return raw[1:].decode(errors="replace") if raw and raw[0] != 0 else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=["preflight", *CASES])
    parser.add_argument("--contract", required=True)
    parser.add_argument("--version", choices=SOURCES, default="v2")
    parser.add_argument("--fixture", type=Path, default=ROOT / "fixtures/synthetic-happy/manifest-png.json")
    args = parser.parse_args()
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", args.contract) or int(args.contract,16) == 0:
        parser.error("Provide the deployed probe address, not an escrow address")
    local = (ROOT / "diagnostics" / SOURCES[args.version]).read_bytes()
    actual = base64.b64decode(rpc("gen_getContractCode", [args.contract]))
    if actual != local:
        raise RuntimeError("SOURCE_MISMATCH_STOP")
    info_hex = rpc("gen_call", [call_params(args.contract,"read","info",[])])
    if calldata.decode(bytes.fromhex(info_hex.removeprefix("0x"))) != INFO.replace("-v2|", "-"+args.version+"|"):
        raise RuntimeError("PROBE_IDENTITY_MISMATCH_STOP")
    print("EXACT_SOURCE_VERIFIED", hashlib.sha256(actual).hexdigest(), flush=True)
    if args.case == "preflight":
        return
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    run_args = arguments(args.case, fixture)
    expected_binding = hashlib.sha256(json.dumps(run_args,separators=(",",":")).encode()).hexdigest()
    folder = ROOT / ".diagnostic-private"
    folder.mkdir(exist_ok=True)
    checkpoint = folder / ("image-probe-" + args.contract.lower() + "-" + args.case + "-" + expected_binding + ".json")
    if checkpoint.exists():
        raise RuntimeError("CASE_ALREADY_CHECKPOINTED: inspect the previous outcome before authorizing any repeat")
    record = {"contract":args.contract,"case":args.case,"args":run_args,"version":args.version,
              "source_sha256":hashlib.sha256(actual).hexdigest(),
              "started_at":datetime.now(timezone.utc).isoformat(),
              "kind":"remote unsigned leader snapshot simulation; not a transaction or consensus proof",
              "status":"INTENT_SAVED", "attached_value":0}
    checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")
    try:
        receipt = rpc("sim_call", [call_params(args.contract,"write","run",run_args)])
        record.update(status="RECEIPT_SAVED",receipt=receipt)
    except Exception as exc:
        record.update(status="RPC_UNRESOLVED",error_type=type(exc).__name__)
        checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")
        raise
    checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")
    print(json.dumps({"case":args.case,"execution_result":receipt.get("execution_result"),
                      "result":decode_result(receipt),"error":decode_error(receipt),
                      "genvm_result":receipt.get("genvm_result")},indent=2))
    if receipt.get("execution_result") != "SUCCESS":
        raise SystemExit(2)
    result = decode_result(receipt)
    if args.case == "control":
        if result != "CONTROL_OK": raise RuntimeError("CONTROL_RESULT_MISMATCH")
    else:
        parsed = json.loads(result)
        expected = "FETCH_VERIFIED" if args.case == "fetch" else "MODEL_ROUNDTRIP"
        if parsed["status"] != expected or parsed["images"] != len(run_args[1]) or parsed["binding"] != expected_binding:
            raise RuntimeError("DIAGNOSTIC_READBACK_MISMATCH")
    record["status"] = "DIAGNOSTIC_VERIFIED_NOT_SERVICE_PROOF"
    checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")


if __name__ == "__main__":
    main()
