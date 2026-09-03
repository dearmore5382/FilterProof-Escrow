"""Export address-scoped allowlisted simulation evidence; no network calls or raw config."""
import argparse
import json
import re
from pathlib import Path
from diagnostics.run_image_probe import decode_result, decode_error

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", args.contract):
        parser.error("Expected a contract address")
    rows = []
    for path in sorted((ROOT / ".diagnostic-private").glob("image-probe-*.json")):
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved["contract"].lower() != args.contract.lower():
            continue
        receipt = saved.get("receipt", {})
        vm = receipt.get("genvm_result") or {}
        rows.append({"case":saved["case"], "started_at":saved["started_at"],
                     "source_sha256":saved["source_sha256"], "args":saved["args"],
                     "checkpoint_status":saved["status"],
                     "execution_result":receipt.get("execution_result"),
                     "result":decode_result(receipt) if "result" in receipt else None,
                     "error":decode_error(receipt) if "result" in receipt else None,
                     "stdout":vm.get("stdout"), "stderr":vm.get("stderr")})
    if not rows:
        raise SystemExit("No matching saved evidence")
    report = {"contract":args.contract, "rpc":"https://studio.genlayer.com/api",
              "evidence_kind":"remote unsigned leader snapshot simulations; NOT transactions or consensus evidence",
              "signed_transactions":0, "attached_value":0, "cases":rows,
              "limits":"No service verdict or payout proved. Raw model response on failure is not recorded by this probe."}
    output = ROOT / "verification" / ("image-probe-" + args.contract.lower() + "-results.json")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
