"""Export validated allowlisted preview evidence without raw node configuration."""
import argparse
import json
import re
from diagnostics.run_escrow_preview import ROOT, SOURCE_SHA256, CASES, validate_receipt
from diagnostics.run_image_probe import decode_result, decode_error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", args.contract):
        parser.error("Expected contract address")
    rows = []
    for path in sorted((ROOT / ".diagnostic-private").glob("escrow-preview-*.json")):
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved["contract"].lower() != args.contract.lower(): continue
        if saved["source_sha256"] != SOURCE_SHA256: raise RuntimeError("Evidence source mismatch")
        receipt = saved.get("receipt", {})
        vm = receipt.get("genvm_result") or {}
        if saved["status"] == "PREVIEW_EXPECTATION_MET_NOT_LIFECYCLE_PROOF":
            validate_receipt(saved["case"],receipt)
            if saved.get("counts_before") != "0|0" or saved.get("counts_after") != "0|0":
                raise RuntimeError("Evidence counts mismatch")
        rows.append({"case":saved["case"],"started_at":saved["started_at"],"args":saved["args"],
                     "status":saved["status"],"counts_before":saved.get("counts_before"),
                     "counts_after":saved.get("counts_after"),"execution_result":receipt.get("execution_result"),
                     "result":decode_result(receipt) if "result" in receipt else None,
                     "error":decode_error(receipt) if "result" in receipt else None,
                     "stdout":vm.get("stdout"),"stderr":vm.get("stderr")})
    if not rows: raise RuntimeError("No matching evidence")
    complete = (len(rows) == len(CASES) and {r["case"] for r in rows} == set(CASES)
                and all(r["status"] == "PREVIEW_EXPECTATION_MET_NOT_LIFECYCLE_PROOF" for r in rows))
    report = {"contract":args.contract,"source_sha256":SOURCE_SHA256,"rpc":"https://studio.genlayer.com/api",
              "evidence_kind":"remote unsigned leader preview simulations; not finalized transactions or consensus proof",
              "frozen_preview_matrix_passed":complete,"signed_transactions":0,"attached_value":0,
              "funded_lifecycle_verified":False,"multi_validator_consensus_verified":False,
              "fixture_is_synthetic":True,"cases":rows}
    output = ROOT / "verification" / ("escrow-preview-"+args.contract.lower()+"-results.json")
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(str(output))
    print("FROZEN_PREVIEW_MATRIX_PASSED",complete)


if __name__ == "__main__":
    main()
