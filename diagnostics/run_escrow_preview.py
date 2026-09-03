"""One source-verified, unsigned preview on a fresh user-deployed escrow."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from genlayer_py.abi import calldata
from diagnostics.read_probe import rpc
from diagnostics.run_image_probe import call_params, decode_result, decode_error

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = "326e46f225bc2e88e0cefb581a8b5cbf450f3322017993098794bdcf5d3ff2a9"
MANIFEST_URL = "https://raw.githubusercontent.com/dearmore5382/FilterProof-Escrow/56ca76cb35b4835f2d64b30cdce49aecc80c2942/fixtures/synthetic-happy/manifest.json"
MANIFEST_SHA256 = "35aad96156bd14fa6e3797ee88a8e71461d208caa8472c633027b5db4b9cd992"
CASES = ("positive", "wrong-manifest-hash", "cross-job", "invalid-url")


def case_arguments(case):
    args = [MANIFEST_URL, MANIFEST_SHA256, 0, "DEMO-SITE-01", "FP-TEST-001",
            "0xA63DE24e30C88FB1019E8956654730316e36eDBE", "SED-5M, CARBON-10, UF-01"]
    if case == "wrong-manifest-hash": args[1] = "0"*64
    elif case == "cross-job": args[2] = 1
    elif case == "invalid-url": args[0] = "http://localhost/not-allowed"
    elif case != "positive": raise ValueError("Unknown preview case")
    return args


def validate_receipt(case, receipt):
    if case == "invalid-url":
        if receipt.get("execution_result") != "ERROR" or decode_error(receipt) != "INVALID_MANIFEST_URL":
            raise RuntimeError("EXPECTED_INPUT_REJECTION_NOT_OBSERVED")
        return
    if receipt.get("execution_result") != "SUCCESS":
        raise RuntimeError("PREVIEW_EXECUTION_FAILED_STOP")
    parsed = json.loads(decode_result(receipt))
    if set(parsed) != {"scope", "observation", "outcome"} or parsed["scope"] != "PREVIEW_ONLY_NO_PAYMENT_AUTHORIZATION":
        raise RuntimeError("PREVIEW_SCHEMA_MISMATCH")
    expected = {"verdict":"SERVICE_CONFIRMED", "reason":"ALL_CHECKS_CONFIRMED"} if case == "positive" else {
        "verdict":"MATERIAL_FAILURE", "reason":"MANIFEST_BINDING_MISMATCH"}
    if parsed["outcome"] != expected:
        raise RuntimeError("PREVIEW_OUTCOME_DIFFERS_FROM_FROZEN_EXPECTATION")
    expected_observation = {"binding_status":"MATCH", "asset_identity":"MATCH",
                            "filter_replacement":"COMPLETE", "before_after_continuity":"CONSISTENT",
                            "pressure_evidence":"PLAUSIBLE", "tamper_signal":"NONE"}
    if case != "positive":
        expected_observation = {k:("MISMATCH" if k == "binding_status" else "UNCERTAIN") for k in expected_observation}
    if parsed["observation"] != expected_observation:
        raise RuntimeError("PREVIEW_OBSERVATIONS_MISMATCH")


def verify_fresh(address):
    code = base64.b64decode(rpc("gen_getContractCode", [address]))
    if hashlib.sha256(code).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("DEPLOYED_SOURCE_MISMATCH")
    output = rpc("gen_call", [call_params(address,"read","get_counts",[])])
    counts = calldata.decode(bytes.fromhex(output.removeprefix("0x")))
    if counts != "0|0": raise RuntimeError("EXPECTED_FRESH_UNFUNDED_ESCROW_STOP")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("preflight", *CASES))
    parser.add_argument("--contract", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", args.contract) or int(args.contract,16) == 0:
        parser.error("Provide the newly deployed escrow address, not a probe")
    if hashlib.sha256((ROOT / "contracts/FilterProofEscrow.py").read_bytes()).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("LOCAL_SOURCE_CHANGED_REVIEW_REQUIRED")
    counts = verify_fresh(args.contract)
    print("EXACT_ESCROW_SOURCE_VERIFIED; COUNTS",counts,flush=True)
    if args.case == "preflight": return
    values = case_arguments(args.case)
    binding = hashlib.sha256(calldata.encode(values)).hexdigest()
    checkpoint = ROOT / ".diagnostic-private" / ("escrow-preview-"+args.contract.lower()+"-"+args.case+"-"+binding+".json")
    checkpoint.parent.mkdir(exist_ok=True)
    if checkpoint.exists(): raise RuntimeError("CASE_ALREADY_CHECKPOINTED_STOP")
    record = {"contract":args.contract,"source_sha256":SOURCE_SHA256,"case":args.case,"args":values,
              "started_at":datetime.now(timezone.utc).isoformat(),"counts_before":counts,
              "kind":"remote unsigned leader preview simulation; not payout, consensus or live lifecycle evidence",
              "signed_transactions":0,"attached_value":0,"status":"INTENT_SAVED"}
    checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")
    try:
        receipt = rpc("sim_call", [call_params(args.contract,"write","preview_proof",values)])
        record.update(status="RECEIPT_SAVED",receipt=receipt)
    except Exception as exc:
        record.update(status="RPC_UNRESOLVED",error_type=type(exc).__name__)
        raise
    finally:
        checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")
    print(json.dumps({"case":args.case,"execution_result":receipt.get("execution_result"),
                      "result":decode_result(receipt),"error":decode_error(receipt),
                      "genvm_result":receipt.get("genvm_result")},indent=2),flush=True)
    record["counts_after"] = verify_fresh(args.contract)
    checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")
    validate_receipt(args.case, receipt)
    record["status"] = "PREVIEW_EXPECTATION_MET_NOT_LIFECYCLE_PROOF"
    checkpoint.write_text(json.dumps(record,indent=2),encoding="utf-8")


if __name__ == "__main__":
    main()
