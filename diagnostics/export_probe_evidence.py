"""Export an allowlisted diagnostic ledger, never full node configuration."""
import base64
import json
from pathlib import Path
from genlayer_py.abi import calldata

ROOT = Path(__file__).resolve().parents[1]
rows = []
for case in ("control", "fetch", "text", "json", "one-text"):
    receipt = json.loads((ROOT / ".diagnostic-private" / ("probe-simulation-" + case + ".json")).read_text())
    vm = receipt.get("genvm_result") or {}
    encoded = base64.b64decode(receipt["result"])
    result = calldata.decode(encoded[1:]) if encoded[0] == 0 else encoded[1:].decode(errors="replace")
    rows.append({"case":case, "execution_result":receipt["execution_result"],
                 "mode":receipt.get("mode"), "result":result,
                 "stdout":vm.get("stdout"), "stderr":vm.get("stderr"),
                 "rpc_error":receipt.get("rpc_error")})
report = {"date":"2026-09-03", "rpc":"https://studio.genlayer.com/api",
          "contract":"0x9D1F3F657530C83500669ddBFa65568F6A185c18",
          "source_sha256":"5f5f1649e791f1eb30f1c3a39ab34662141642ef727bc8fefcf5cb8654b704c5",
          "evidence_kind":"remote leader snapshot simulations; not transactions or consensus evidence",
          "signed_transactions":0, "attached_value":0,
          "redactions":"node_config, contract_state and other non-allowlisted fields omitted",
          "cases":rows,
          "additional_observation":"one-json also returned INVALID_IMAGE; its error was observed before the recorder saved RPC error receipts, so no raw snapshot is claimed for that case"}
output = ROOT / "verification/probe-simulation-results.json"
output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(output)
