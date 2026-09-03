"""Checkpointed 0.01 GEN expiry/recovery lifecycle for live-matrix F7."""
import getpass
import json
from datetime import datetime, timedelta, timezone
import sys

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet

from diagnostics.read_probe import redact, rpc as simulation_rpc
from diagnostics.run_image_probe import decode_error, decode_result
from diagnostics.run_escrow_preview import ROOT, SOURCE_SHA256
from verification.run_failure_smoke import (
    ADDRESS, BOUNTY, OPERATOR, TECHNICIAN, call_params, normalized_tx_result, parity, view,
)
from verification.run_funded_lifecycle import balance, rpc as chain_rpc


JOURNAL = ROOT / ".diagnostic-private" / ("expiry-recovery-" + ADDRESS.lower() + ".json")
PUBLIC = ROOT / "verification" / ("expiry-recovery-" + ADDRESS.lower() + ".json")
PHASES = ("create", "fund", "recover")
METHODS = ("create_job", "fund_job", "recover_expired")


def save(report):
    JOURNAL.parent.mkdir(exist_ok=True)
    JOURNAL.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")


def public_save(report):
    clean = redact({key: value for key, value in report.items() if key != "kind"})
    clean["evidence_kind"] = report["kind"]
    PUBLIC.write_text(json.dumps(clean, indent=2, default=str) + "\n", encoding="utf-8")


def snapshot(job_id):
    return {
        "counts": view("get_counts"), "job": view("get_job", [job_id]),
        "accounting": view("get_accounting", [job_id]), "contract_balance": balance(ADDRESS),
    }


def action(report, index):
    job_id = report["job_id"]
    create_args = [
        "Synthetic expiry recovery", "DEMO-EXPIRY-01", "FP-EXPIRY-001",
        "SED-5M, CARBON-10, UF-01", TECHNICIAN, BOUNTY, report["recovery_after"],
    ]
    args = (create_args, [job_id], [job_id])[index]
    expected = (str(job_id), "FUNDED", "EXPIRED_REFUNDED")[index]
    # Recovery is intentionally permissionless and sent by the technician wallet.
    actor = TECHNICIAN if index == 2 else OPERATOR
    return {"phase": PHASES[index], "method": METHODS[index], "args": args,
            "actor": actor, "value": BOUNTY if index == 1 else 0, "expected": expected}


def validate_state(report, index, state):
    job_id = report["job_id"]
    expected_status = ("DRAFT", "FUNDED", "EXPIRED_REFUNDED")[index]
    if state["counts"] != f"{job_id + 1}|{report['attempt_count_before']}":
        raise RuntimeError("COUNTS_MISMATCH")
    if state["job"].split("|")[0] != expected_status or state["job"].split("|")[-1] != "0":
        raise RuntimeError("JOB_STATE_MISMATCH")
    held = BOUNTY if index == 1 else 0
    refunded = BOUNTY if index == 2 else 0
    if state["accounting"].split("|")[:4] != [str(BOUNTY), str(held), "0", str(refunded)]:
        raise RuntimeError("ACCOUNTING_MISMATCH")
    if state["contract_balance"] != held:
        raise RuntimeError("CONTRACT_BALANCE_MISMATCH")


def main():
    if not sys.stdin.isatty():
        raise RuntimeError("INTERACTIVE_NO_ECHO_TERMINAL_REQUIRED")
    keys = json.loads(getpass.getpass("KEY_INPUT_REQUIRED_NO_ECHO: "))
    accounts = [create_account(account_private_key="0x" + key.removeprefix("0x")) for key in keys]
    del keys
    clients = {account.address.lower(): create_client(chain=studionet, account=account) for account in accounts}
    if set(clients) != {OPERATOR.lower(), TECHNICIAN.lower()}:
        raise RuntimeError("AUTHORIZED_WALLET_MISMATCH")
    parity()
    if JOURNAL.exists():
        report = json.loads(JOURNAL.read_text(encoding="utf-8"))
        if report["source_sha256"] != SOURCE_SHA256:
            raise RuntimeError("JOURNAL_SOURCE_MISMATCH")
    else:
        job_count, attempt_count = (int(item) for item in view("get_counts").split("|"))
        if job_count != 3 or attempt_count != 3 or not view("get_job", [2]).startswith("REFUNDED|"):
            raise RuntimeError("EXPECTED_PRIOR_REFUND_STATE")
        if balance(ADDRESS) != 0 or balance(OPERATOR) < BOUNTY:
            raise RuntimeError("BALANCE_PREFLIGHT_FAILED")
        report = {
            "contract": ADDRESS, "source_sha256": SOURCE_SHA256,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "kind": "three signed multi-validator writes plus one unsigned early-recovery simulation",
            "job_id": job_count, "attempt_count_before": attempt_count, "bounty_wei": BOUNTY,
            "recovery_after": (datetime.now(timezone.utc) + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "initial_balances": {"operator": balance(OPERATOR), "technician": balance(TECHNICIAN),
                                 "contract": balance(ADDRESS)},
            "steps": [], "status": "READY_FOR_NEXT",
        }
        save(report)
    print(json.dumps({"ready": True, "status": report["status"], "job_id": report["job_id"],
                      "recovery_after": report["recovery_after"], "completed_steps": len(report["steps"])}), flush=True)

    for line in sys.stdin:
        command = line.strip()
        if command == "quit":
            return
        try:
            if command == "next":
                index = len(report["steps"])
                if report["status"] != "READY_FOR_NEXT" or index >= len(PHASES):
                    raise RuntimeError("NEXT_NOT_ALLOWED")
                if index == 2 and datetime.now(timezone.utc) < datetime.fromisoformat(report["recovery_after"].replace("Z", "+00:00")):
                    raise RuntimeError("LOCAL_DEADLINE_NOT_REACHED")
                if index:
                    validate_state(report, index - 1, snapshot(report["job_id"]))
                row = action(report, index)
                row.update(status="INTENT_SAVED", submitted_at=datetime.now(timezone.utc).isoformat())
                if index == 2:
                    report["operator_before_recovery"] = balance(OPERATOR)
                report["steps"].append(row)
                report["status"] = "SUBMISSION_INTENT_SAVED"
                save(report)
                tx_hash = clients[row["actor"].lower()].write_contract(
                    address=ADDRESS, function_name=row["method"], args=row["args"], value=row["value"], leader_only=False
                )
                row.update(hash=str(tx_hash), status="SUBMITTED")
                report["status"] = "SUBMITTED"
                save(report)
                print(json.dumps({"phase": row["phase"], "hash": row["hash"], "value": row["value"]}), flush=True)
            elif command == "poll":
                row = report["steps"][-1]
                if not row.get("hash"):
                    raise RuntimeError("UNKNOWN_SUBMISSION_DO_NOT_RESEND")
                tx = chain_rpc("eth_getTransactionByHash", [row["hash"]])
                if not tx:
                    raise RuntimeError("TX_NOT_FOUND_KEEP_HASH")
                print(json.dumps({"phase": row["phase"], "hash": row["hash"], "status": tx.get("status"),
                                  "consensus": tx.get("result_name")}), flush=True)
                if tx.get("status") == "FINALIZED":
                    if tx.get("result_name") != "MAJORITY_AGREE" or normalized_tx_result(tx) != row["expected"]:
                        raise RuntimeError("FINALITY_RESULT_MISMATCH")
                    index = PHASES.index(row["phase"])
                    state = snapshot(report["job_id"])
                    validate_state(report, index, state)
                    row.update(status="READBACK_VERIFIED", receipt=tx, readback=state)
                    report["status"] = "READY_FOR_EFFECT" if index == 2 else "READY_FOR_EARLY" if index == 1 else "READY_FOR_NEXT"
                    save(report)
                    print(json.dumps({"phase": row["phase"], "verified": True,
                                      "job_status": state["job"].split("|")[0], "accounting": state["accounting"]}), flush=True)
            elif command == "early":
                if report["status"] != "READY_FOR_EARLY":
                    raise RuntimeError("EARLY_CHECK_NOT_ALLOWED")
                before = snapshot(report["job_id"])
                receipt = simulation_rpc("sim_call", [call_params(TECHNICIAN, "recover_expired", [report["job_id"]])])
                row = {"case": "recover-before-deadline", "execution_result": receipt.get("execution_result"),
                       "result": decode_result(receipt), "error": decode_error(receipt), "expected": "RECOVERY_TOO_EARLY"}
                report["early_recovery_simulation"] = row
                save(report)
                if row["execution_result"] != "SUCCESS" or row["result"] != row["expected"]:
                    raise RuntimeError("EARLY_RECOVERY_EXPECTATION_MISMATCH")
                if snapshot(report["job_id"]) != before:
                    raise RuntimeError("EARLY_SIMULATION_CHANGED_STATE")
                report["status"] = "READY_FOR_NEXT"
                save(report)
                print(json.dumps(row), flush=True)
            elif command == "effect":
                if report["status"] != "READY_FOR_EFFECT":
                    raise RuntimeError("EFFECT_NOT_ALLOWED")
                parent = chain_rpc("eth_getTransactionByHash", [report["steps"][-1]["hash"]])
                children = parent.get("triggered_transactions") or []
                receipts = [chain_rpc("eth_getTransactionByHash", [child]) for child in children]
                matching = [tx for tx in receipts if tx and tx.get("status") == "FINALIZED" and tx.get("type") == 0
                            and str(tx.get("from_address")).lower() == ADDRESS.lower()
                            and str(tx.get("to_address")).lower() == OPERATOR.lower()
                            and tx.get("triggered_by") == parent["hash"] and int(tx.get("value", -1)) == BOUNTY]
                if len(receipts) != 1 or len(matching) != 1:
                    raise RuntimeError("RECOVERY_CHILD_NOT_FINALIZED")
                final_balances = {"operator": balance(OPERATOR), "technician": balance(TECHNICIAN),
                                  "contract": balance(ADDRESS)}
                if final_balances["operator"] - report["operator_before_recovery"] != BOUNTY or final_balances["contract"] != 0:
                    raise RuntimeError("RECOVERY_BALANCE_EFFECT_MISMATCH")
                report.update(child_receipts=receipts, final_balances=final_balances, status="EXPIRY_RECOVERY_PASSED")
                save(report)
                public_save(report)
                print(json.dumps({"recovery_verified": True, "child": matching[0]["hash"],
                                  "operator_received": BOUNTY, "contract_balance": 0}), flush=True)
            else:
                raise ValueError("UNKNOWN_ACTION")
        except Exception as exc:
            print(json.dumps({"action_failed": command, "error_type": type(exc).__name__,
                              "journal_preserved": True}), flush=True)
        print("READY_FOR_ACTION", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"fatal_error_type": type(exc).__name__}), flush=True)
        raise SystemExit(1)
