"""Unsigned constructor snapshot with explicit UTC; never broadcasts a deployment.

Only the known stateless v3 probe is used as the snapshot anchor. Source bytes
and info must match before and after. A checkpoint prevents implicit retries.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from diagnostics.read_probe import rpc, SENDER
from diagnostics.run_image_probe import call_params, decode_result, decode_error

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = "0x9Bed86f3ccf45b778c09e33A91aD14e5C65c3857"
ANCHOR_HASH = "9c20d05aa62bc52d0e4280af6789dcd745675eaee0a986f8b209d19ced605ddf"
INFO = "FilterProofImageProbe-v3|URL_SHA256_INPUTS|DIAGNOSTIC_ONLY|SEND_ZERO_VALUE"


def params(source, args, timestamp):
    return {"type":"deploy", "to":ANCHOR, "from":SENDER, "value":"0x0",
            "sim_config":{"genvm_datetime":timestamp},
            "data":serialize([source, calldata.encode({"args":args}), b'\x00'])}


def verify_anchor():
    code = base64.b64decode(rpc("gen_getContractCode", [ANCHOR]))
    if hashlib.sha256(code).hexdigest() != ANCHOR_HASH:
        raise RuntimeError("ANCHOR_SOURCE_MISMATCH")
    encoded = rpc("gen_call", [call_params(ANCHOR, "read", "info", [])])
    if calldata.decode(bytes.fromhex(encoded.removeprefix("0x"))) != INFO:
        raise RuntimeError("ANCHOR_INFO_MISMATCH")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--args-file", type=Path)
    args = parser.parse_args()
    source = args.source.read_bytes()
    values = json.loads(args.args_file.read_text(encoding="utf-8")) if args.args_file else []
    if not isinstance(values, list):
        parser.error("Constructor arguments must be a JSON array")
    binding = hashlib.sha256(source + b'\x00' + calldata.encode(values)).hexdigest()
    folder = ROOT / ".diagnostic-private"
    folder.mkdir(exist_ok=True)
    checkpoint = folder / ("constructor-snapshot-" + binding + ".json")
    if checkpoint.exists():
        raise RuntimeError("SNAPSHOT_ALREADY_CHECKPOINTED_STOP")
    verify_anchor()
    stamp = datetime.now(timezone.utc).isoformat()
    record = {"kind":"remote unsigned disposable constructor snapshot; not a deployment, transaction or consensus proof",
              "anchor":ANCHOR,"anchor_sha256":ANCHOR_HASH,"source":args.source.name,
              "source_sha256":hashlib.sha256(source).hexdigest(),"input_binding":binding,
              "args":values,"started_at":stamp,"signed_transactions":0,"attached_value":0,
              "status":"INTENT_SAVED"}
    checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")
    print("ANCHOR_VERIFIED; UNSIGNED_SNAPSHOT_ONLY; UTC", stamp, flush=True)
    try:
        receipt = rpc("sim_call", [params(source, values, stamp)])
        record.update(status="RECEIPT_SAVED", receipt=receipt)
    except Exception as exc:
        record.update(status="RPC_UNRESOLVED",error_type=type(exc).__name__)
        raise
    finally:
        checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")
        verify_anchor()
        record["anchor_unchanged"] = True
        checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")
    print(json.dumps({"checkpoint":str(checkpoint),"execution_result":receipt.get("execution_result"),
                      "result":decode_result(receipt),"error":decode_error(receipt),
                      "genvm_result":receipt.get("genvm_result"),"anchor_unchanged":True},indent=2))
    if receipt.get("execution_result") != "SUCCESS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
