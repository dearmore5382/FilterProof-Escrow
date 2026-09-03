"""Checkpointed 0.01 GEN two-failure refund lifecycle on the deployed escrow."""
import getpass
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet

from diagnostics.read_probe import redact
from diagnostics.run_escrow_preview import MANIFEST_URL, ROOT, SOURCE_SHA256
from verification.run_failure_smoke import (
    ADDRESS, BOUNTY, OPERATOR, TECHNICIAN, normalized_tx_result, parity, view,
)
from verification.run_funded_lifecycle import balance, rpc as chain_rpc


WRONG_DIGEST = "0" * 64
JOURNAL = ROOT / ".diagnostic-private" / ("refund-path-" + ADDRESS.lower() + ".json")
PUBLIC = ROOT / "verification" / ("refund-path-" + ADDRESS.lower() + ".json")
PHASES = ("create", "fund", "submit-1", "assess-1", "submit-2", "assess-2", "refund")
METHODS = ("create_job", "fund_job", "submit_proof", "assess_proof", "submit_proof", "assess_proof", "execute_refund")
EXPECTED = (None, "FUNDED", None, "CORRECTION_REQUIRED", None, "REFUND_AUTHORIZED", "REFUNDED")
STATUSES = ("DRAFT", "FUNDED", "PROOF_READY", "CORRECTION_REQUIRED", "PROOF_READY", "REFUND_AUTHORIZED", "REFUNDED")


def save(report):
    JOURNAL.parent.mkdir(exist_ok=True)
    JOURNAL.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")


def public_save(report):
    clean = redact({key: value for key, value in report.items() if key != "kind"})
    clean["evidence_kind"] = report["kind"]
    PUBLIC.write_text(json.dumps(clean, indent=2, default=str) + "\n", encoding="utf-8")


def snapshot(report):
    job_id = report["job_id"]
    result = {
        "counts": view("get_counts"), "job": view("get_job", [job_id]),
        "accounting": view("get_accounting", [job_id]), "contract_balance": balance(ADDRESS),
    }
    for attempt_id in report["attempt_ids"]:
        result[f"attempt_{attempt_id}"] = view("get_attempt", [attempt_id])
    return result


def action(report, index):
    job_id = report["job_id"]
    attempt_ids = report["attempt_ids"]
    create_args = [
        "Synthetic binding-failure refund", "DEMO-REFUND-01", "FP-REFUND-001",
        "SED-5M, CARBON-10, UF-01", TECHNICIAN, BOUNTY, report["recovery_after"],
    ]
    args = (create_args, [job_id], [job_id, MANIFEST_URL, WRONG_DIGEST], [job_id],
            [job_id, MANIFEST_URL, WRONG_DIGEST], [job_id], [job_id])[index]
    actor = TECHNICIAN if index in (2, 4) else OPERATOR
    expected = EXPECTED[index]
    if index == 0:
        expected = str(job_id)
    elif index == 2:
        expected = str(attempt_ids[0])
    elif index == 4:
        expected = str(attempt_ids[1])
    return {"phase": PHASES[index], "method": METHODS[index], "args": args, "actor": actor,
            "value": BOUNTY if index == 1 else 0, "expected": expected}


def validate_state(report, index, state):
    job_id = report["job_id"]
    initial_attempt = report["attempt_ids"][0]
    global_attempts = initial_attempt + (0 if index < 2 else 1 if index < 4 else 2)
    if state["counts"] != f"{job_id + 1}|{global_attempts}":
        raise RuntimeError("COUNTS_MISMATCH")
    parts = state["job"].split("|")
    expected_attempts = 0 if index < 2 else 1 if index < 4 else 2
    if parts[0] != STATUSES[index] or parts[-1] != str(expected_attempts):
        raise RuntimeError("JOB_STATE_MISMATCH")
    held = BOUNTY if 1 <= index <= 5 else 0
    refunded = BOUNTY if index == 6 else 0
    if state["accounting"].split("|")[:4] != [str(BOUNTY), str(held), "0", str(refunded)]:
        raise RuntimeError("ACCOUNTING_MISMATCH")
    if state["contract_balance"] != held:
        raise RuntimeError("CONTRACT_BALANCE_MISMATCH")
    if index >= 2:
        first = state[f"attempt_{initial_attempt}"].split("|")
        if first[1:3] != [str(job_id), "1"] or first[5] != WRONG_DIGEST:
            raise RuntimeError("FIRST_ATTEMPT_BINDING_MISMATCH")
        if index == 2 and first[0] != "READY":
            raise RuntimeError("FIRST_ATTEMPT_NOT_READY")
        if index >= 3 and first[:1] != ["ASSESSED"] or index >= 3 and first[3:5] != ["MATERIAL_FAILURE", "MANIFEST_BINDING_MISMATCH"]:
            raise RuntimeError("FIRST_ATTEMPT_ASSESSMENT_MISMATCH")
    if index >= 4:
        second = state[f"attempt_{initial_attempt + 1}"].split("|")
        if second[1:3] != [str(job_id), "2"] or second[5] != WRONG_DIGEST:
            raise RuntimeError("SECOND_ATTEMPT_BINDING_MISMATCH")
        if index == 4 and second[0] != "READY":
            raise RuntimeError("SECOND_ATTEMPT_NOT_READY")
        if index >= 5 and (second[0] != "ASSESSED" or second[3:5] != ["MATERIAL_FAILURE", "MANIFEST_BINDING_MISMATCH"]):
            raise RuntimeError("SECOND_ATTEMPT_ASSESSMENT_MISMATCH")


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
        if job_count != 2 or attempt_count != 1 or not view("get_job", [1]).startswith("CANCELLED|"):
            raise RuntimeError("EXPECTED_FAILURE_SMOKE_TERMINAL_STATE")
        if balance(ADDRESS) != 0 or balance(OPERATOR) < BOUNTY:
            raise RuntimeError("BALANCE_PREFLIGHT_FAILED")
        report = {
            "contract": ADDRESS, "source_sha256": SOURCE_SHA256,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "kind": "seven signed multi-validator writes for a synthetic binding-failure refund lifecycle",
            "job_id": job_count, "attempt_ids": [attempt_count, attempt_count + 1],
            "bounty_wei": BOUNTY,
            "recovery_after": (datetime.now(timezone.utc) + timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "initial_balances": {"operator": balance(OPERATOR), "technician": balance(TECHNICIAN),
                                 "contract": balance(ADDRESS)},
            "steps": [], "status": "READY_FOR_NEXT",
        }
        save(report)
    print(json.dumps({"ready": True, "status": report["status"], "job_id": report["job_id"],
                      "completed_steps": len(report["steps"]), "bounty_wei": BOUNTY}), flush=True)

    for line in sys.stdin:
        command = line.strip()
        if command == "quit":
            return
        try:
            if command == "next":
                index = len(report["steps"])
                if report["status"] != "READY_FOR_NEXT" or index >= len(PHASES):
                    raise RuntimeError("NEXT_NOT_ALLOWED")
                if index:
                    validate_state(report, index - 1, snapshot(report))
                row = action(report, index)
                row.update(status="INTENT_SAVED", submitted_at=datetime.now(timezone.utc).isoformat())
                if index == 6:
                    report["operator_before_refund"] = balance(OPERATOR)
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
                    state = snapshot(report)
                    index = PHASES.index(row["phase"])
                    validate_state(report, index, state)
                    row.update(status="READBACK_VERIFIED", receipt=tx, readback=state)
                    report["status"] = "READY_FOR_EFFECT" if index == 6 else "READY_FOR_NEXT"
                    save(report)
                    print(json.dumps({"phase": row["phase"], "verified": True, "job_status": state["job"].split("|")[0],
                                      "accounting": state["accounting"]}), flush=True)
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
                    raise RuntimeError("REFUND_CHILD_NOT_FINALIZED")
                final_balances = {"operator": balance(OPERATOR), "technician": balance(TECHNICIAN),
                                  "contract": balance(ADDRESS)}
                if final_balances["operator"] - report["operator_before_refund"] != BOUNTY or final_balances["contract"] != 0:
                    raise RuntimeError("REFUND_BALANCE_EFFECT_MISMATCH")
                report.update(child_receipts=receipts, final_balances=final_balances,
                              status="REFUND_PATH_PASSED")
                save(report)
                public_save(report)
                print(json.dumps({"refund_verified": True, "child": matching[0]["hash"],
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
