"""One-shot unsigned 404/oversized source previews on the deployed escrow."""
import base64
from datetime import datetime, timezone
import hashlib
import json

from genlayer_py.abi import calldata

from diagnostics.read_probe import rpc
from diagnostics.run_image_probe import call_params, decode_error, decode_result
from diagnostics.run_escrow_preview import ROOT, SOURCE_SHA256
from verification.run_failure_smoke import ADDRESS, OPERATOR, TECHNICIAN, view


CASES = (
    ("manifest-404", "https://raw.githubusercontent.com/dearmore5382/FilterProof-Escrow/c28700ffda3067384c096da00f72e73be1959ec2/does-not-exist.json"),
    ("manifest-oversized", "https://raw.githubusercontent.com/dearmore5382/FilterProof-Escrow/c28700ffda3067384c096da00f72e73be1959ec2/contracts/FilterProofEscrow.py"),
)
CHECKPOINT = ROOT / ".diagnostic-private" / ("source-failure-preview-" + ADDRESS.lower() + ".json")
PUBLIC = ROOT / "verification" / ("source-failure-preview-" + ADDRESS.lower() + ".json")


def snapshot():
    return {"counts": view("get_counts"), "last_job": view("get_job", [3]),
            "last_accounting": view("get_accounting", [3])}


def main():
    deployed = base64.b64decode(rpc("gen_getContractCode", [ADDRESS]))
    if hashlib.sha256(deployed).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("SOURCE_MISMATCH")
    before = snapshot()
    if before["counts"] != "4|3" or not before["last_job"].startswith("EXPIRED_REFUNDED|"):
        raise RuntimeError("EXPECTED_PRIOR_TERMINAL_STATE")
    if CHECKPOINT.exists():
        report = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        if report["contract"].lower() != ADDRESS.lower() or report["source_sha256"] != SOURCE_SHA256:
            raise RuntimeError("CHECKPOINT_SCOPE_MISMATCH")
    else:
        report = {
            "contract": ADDRESS, "source_sha256": SOURCE_SHA256,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "signed_transactions": 0, "attached_value": 0, "before": before,
            "cases": [], "status": "INTENT_SAVED",
            "kind": "unsigned leader preview simulations; not transactions or consensus evidence",
        }
    CHECKPOINT.parent.mkdir(exist_ok=True)
    CHECKPOINT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for name, url in CASES:
        prior = [row for row in report["cases"] if row["case"] == name]
        if prior:
            row = prior[0]
        else:
            args = [url, "0" * 64, 4, "DEMO-SOURCE-FAIL", "FP-SOURCE-FAIL-001", TECHNICIAN,
                    "SED-5M, CARBON-10, UF-01"]
            receipt = rpc("sim_call", [call_params(ADDRESS, "write", "preview_proof", args) | {"from": OPERATOR}])
            row = {"case": name, "url": url, "execution_result": receipt.get("execution_result"),
                   "result": decode_result(receipt), "error": decode_error(receipt),
                   "genvm_result": receipt.get("genvm_result")}
            report["cases"].append(row)
            CHECKPOINT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({key: row[key] for key in ("case", "execution_result", "result", "error")}), flush=True)
        if row["execution_result"] != "SUCCESS" or row["error"] is not None:
            raise RuntimeError("SOURCE_FAILURE_PREVIEW_EXECUTION_FAILED")
        parsed = json.loads(row["result"])
        expected_observation = {key: "UNCERTAIN" for key in (
            "asset_identity", "before_after_continuity", "filter_replacement", "pressure_evidence", "tamper_signal")}
        expected_observation["binding_status"] = "UNAVAILABLE"
        if parsed.get("observation") != expected_observation or parsed.get("outcome") != {
            "verdict": "INSUFFICIENT_EVIDENCE", "reason": "EVIDENCE_UNAVAILABLE"
        }:
            raise RuntimeError("SOURCE_FAILURE_EXPECTATION_MISMATCH")
    report["after"] = snapshot()
    if report["after"] != before:
        raise RuntimeError("SOURCE_FAILURE_PREVIEW_CHANGED_STATE")
    report["status"] = "SOURCE_FAILURE_PREVIEWS_PASSED_NOT_CONSENSUS_PROOF"
    CHECKPOINT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    public = {key: value for key, value in report.items() if key != "kind"}
    public["evidence_kind"] = report["kind"]
    PUBLIC.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    print("SOURCE_FAILURE_PREVIEWS_PASSED_STATE_UNCHANGED", flush=True)


if __name__ == "__main__":
    main()
