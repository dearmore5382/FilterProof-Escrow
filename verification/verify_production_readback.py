"""Read-only verification of the published funded lifecycle.

No private key is loaded and no transaction can be submitted by this script.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from verification.run_funded_lifecycle import ADDRESS, BOUNTY, TECHNICIAN, balance, parity, rpc, view


JOB_ID = 0
SETTLEMENT_TX = "0x83ebce382ad98808764259b883dbd2961e77e0ac81cf128ec88d66215469ef39"
TRANSFER_TX = "0x0190b34ed0e8967295b413cee06a43573de4b0c35296c196ce5b815809f2dcff"


def main() -> None:
    parity()
    job = view("get_job", [JOB_ID]).split("|")
    accounting = view("get_accounting", [JOB_ID]).split("|")
    if job[0] != "PAID":
        raise RuntimeError("JOB_NOT_PAID")
    if accounting[:4] != [str(BOUNTY), "0", str(BOUNTY), "0"]:
        raise RuntimeError("PAID_ACCOUNTING_MISMATCH")

    parent = rpc("eth_getTransactionByHash", [SETTLEMENT_TX])
    child = rpc("eth_getTransactionByHash", [TRANSFER_TX])
    if parent.get("status") != "FINALIZED" or parent.get("result_name") != "MAJORITY_AGREE":
        raise RuntimeError("SETTLEMENT_NOT_FINALIZED_WITH_CONSENSUS")
    if parent.get("triggered_transactions") != [TRANSFER_TX]:
        raise RuntimeError("SETTLEMENT_CHILD_LIST_MISMATCH")
    if not (
        child.get("status") == "FINALIZED"
        and child.get("type") == 0
        and str(child.get("from_address")).lower() == ADDRESS.lower()
        and str(child.get("to_address")).lower() == TECHNICIAN.lower()
        and child.get("triggered_by") == SETTLEMENT_TX
        and int(child.get("value", -1)) == BOUNTY
        and child.get("value_credited") is True
    ):
        raise RuntimeError("NATIVE_TRANSFER_MISMATCH")

    print("source_parity=PASS")
    print("job_0_state=PAID")
    print("accounting_readback=PASS")
    print("parent_finality_consensus=PASS")
    print("native_transfer=PASS")
    print(f"contract_balance_at_check={balance(ADDRESS)}")


if __name__ == "__main__":
    main()
