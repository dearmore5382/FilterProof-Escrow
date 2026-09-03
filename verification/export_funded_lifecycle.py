"""Export only public transaction/readback fields from the private test journal."""
import json
from verification.run_funded_lifecycle import JOURNAL, ROOT, ADDRESS


def transaction_summary(tx):
    fields = ("hash","from_address","to_address","type","value","status","result_name",
              "leader_only","num_of_initial_validators","triggered_by","triggered_transactions",
              "value_credited","created_at")
    result = {k:tx.get(k) for k in fields}
    consensus = tx.get("consensus_data") or {}
    result["votes"] = consensus.get("votes")
    leaders = consensus.get("leader_receipt") or []
    if isinstance(leaders,dict): leaders = [leaders]
    result["executions"] = [{k:r.get(k) for k in ("mode","vote","execution_result","result","nondet_disagree")}
                            for r in leaders]
    validators = consensus.get("validators") or []
    result["validator_executions"] = [{k:r.get(k) for k in ("mode","vote","execution_result","nondet_disagree")}
                                      for r in validators if isinstance(r,dict)]
    return result


def main():
    saved = json.loads(JOURNAL.read_text(encoding="utf-8"))
    report = {k:saved.get(k) for k in ("contract","source_sha256","chain_id","authorized_bounty",
               "recovery_after","initial_balances","technician_before_release","technician_after_release",
               "final_contract_balance","happy_path_verified")}
    report["scope"] = "One disclosed synthetic-fixture testnet funded happy path; not real maintenance or complete adversarial audit"
    report["steps"] = []
    for row in saved["steps"]:
        public = {k:row.get(k) for k in ("phase","method","args","actor","value","expected","status","submitted_at","hash","readback")}
        if row.get("receipt"): public["receipt"] = transaction_summary(row["receipt"])
        report["steps"].append(public)
    report["child_transactions"] = [transaction_summary(t) for t in saved.get("child_receipts",[]) if t]
    output = ROOT / "verification" / ("funded-happy-"+ADDRESS.lower()+".json")
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(output)
    print("HAPPY_PATH_VERIFIED",report.get("happy_path_verified") is True)


if __name__ == "__main__":
    main()
