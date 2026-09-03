"""Checkpointed low-value live failure smoke test for the deployed escrow.

The only signed writes are create_job and cancel_draft, both with zero attached
value. Failure cases are unsigned leader snapshot simulations and therefore are
not consensus evidence. Private keys are read through a no-echo TTY prompt and
never written to disk.
"""
import base64
from datetime import datetime, timedelta, timezone
import getpass
import hashlib
import json
from pathlib import Path
import sys

from genlayer_py import create_account, create_client
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.chains import studionet

from diagnostics.read_probe import redact, rpc as simulation_rpc
from diagnostics.run_image_probe import decode_error, decode_result
from diagnostics.run_escrow_preview import MANIFEST_SHA256, MANIFEST_URL, ROOT, SOURCE_SHA256
from verification.run_funded_lifecycle import balance, rpc as chain_rpc


ADDRESS = "0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29"
OPERATOR = "0x736A168247e3f0C52F7907c9a8fDac572DF9c8bB"
TECHNICIAN = "0xA63DE24e30C88FB1019E8956654730316e36eDBE"
BOUNTY = 10_000_000_000_000_000  # 0.01 GEN; simulations only in this runner.
JOURNAL = ROOT / ".diagnostic-private" / ("failure-smoke-" + ADDRESS.lower() + ".json")
PUBLIC = ROOT / "verification" / ("failure-smoke-" + ADDRESS.lower() + ".json")


def call_params(sender, method, args, value=0):
    return {
        "type": "write", "to": ADDRESS, "from": sender, "value": hex(value),
        "data": serialize([calldata.encode({"method": method, "args": args}), b"\x00"]),
    }


def view(method, args=None):
    data = call_params(OPERATOR, method, args or [])
    data["type"] = "read"
    data["transaction_hash_variant"] = "latest-final"
    raw = simulation_rpc("gen_call", [data])
    return str(calldata.decode(bytes.fromhex(raw.removeprefix("0x"))))


def snapshot(job_id):
    return {
        "counts": view("get_counts"),
        "job": view("get_job", [job_id]),
        "accounting": view("get_accounting", [job_id]),
        "contract_balance": balance(ADDRESS),
    }


def save(report):
    JOURNAL.parent.mkdir(exist_ok=True)
    JOURNAL.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")


def public_save(report):
    clean = redact({k: v for k, v in report.items() if k != "kind"})
    clean["evidence_kind"] = report["kind"]
    PUBLIC.write_text(json.dumps(clean, indent=2, default=str) + "\n", encoding="utf-8")


def parity():
    deployed = base64.b64decode(simulation_rpc("gen_getContractCode", [ADDRESS]))
    if hashlib.sha256(deployed).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("SOURCE_MISMATCH")


def normalized_tx_result(tx):
    leaders = (tx.get("consensus_data") or {}).get("leader_receipt") or []
    if isinstance(leaders, dict):
        leaders = [leaders]
    leaders = [item for item in leaders if item.get("mode") == "leader"]
    if not leaders or leaders[-1].get("execution_result") != "SUCCESS":
        raise RuntimeError("LEADER_EXECUTION_FAILED")
    result = leaders[-1].get("result")
    raw = base64.b64decode(result["raw"] if isinstance(result, dict) else result)
    if not raw or raw[0] != 0:
        raise RuntimeError("SIGNED_WRITE_RETURNED_ERROR")
    return str(calldata.decode(raw[1:]))


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
        counts = view("get_counts")
        job_count, attempt_count = (int(item) for item in counts.split("|"))
        if job_count < 1 or not view("get_job", [0]).startswith("PAID|"):
            raise RuntimeError("PRIOR_PAID_JOB_NOT_FOUND")
        report = {
            "contract": ADDRESS,
            "source_sha256": SOURCE_SHA256,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "kind": "two signed zero-value consensus writes plus unsigned leader failure simulations",
            "job_id": job_count,
            "attempt_count_before": attempt_count,
            "bounty_wei": BOUNTY,
            "recovery_after": (datetime.now(timezone.utc) + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "initial_balances": {
                "operator": balance(OPERATOR), "technician": balance(TECHNICIAN), "contract": balance(ADDRESS)
            },
            "signed": [], "simulations": [], "status": "READY_TO_CREATE",
        }
        save(report)

    job_id = report["job_id"]
    create_args = [
        "Failure-path smoke test", "DEMO-FAIL-01", "FP-FAIL-001", "SED-5M, CARBON-10, UF-01",
        TECHNICIAN, BOUNTY, report["recovery_after"],
    ]
    print(json.dumps({"ready": True, "job_id": job_id, "status": report["status"],
                      "balances": {"operator": balance(OPERATOR), "technician": balance(TECHNICIAN),
                                   "contract": balance(ADDRESS)}}), flush=True)

    for line in sys.stdin:
        command = line.strip()
        if command == "quit":
            return
        try:
            if command == "create":
                if report["status"] != "READY_TO_CREATE" or view("get_counts").split("|")[0] != str(job_id):
                    raise RuntimeError("CREATE_NOT_ALLOWED_OR_ALREADY_SENT")
                row = {"phase": "create", "method": "create_job", "args": create_args, "value": 0,
                       "actor": OPERATOR, "expected": str(job_id), "status": "INTENT_SAVED"}
                report["signed"].append(row)
                report["status"] = "CREATE_INTENT_SAVED"
                save(report)
                tx_hash = clients[OPERATOR.lower()].write_contract(
                    address=ADDRESS, function_name="create_job", args=create_args, value=0, leader_only=False
                )
                row.update(hash=str(tx_hash), status="SUBMITTED")
                report["status"] = "CREATE_SUBMITTED"
                save(report)
                print(json.dumps({"phase": "create", "hash": str(tx_hash)}), flush=True)
            elif command == "cancel":
                if report["status"] != "SIMULATIONS_VERIFIED" or not view("get_job", [job_id]).startswith("DRAFT|"):
                    raise RuntimeError("CANCEL_NOT_ALLOWED")
                row = {"phase": "cancel", "method": "cancel_draft", "args": [job_id], "value": 0,
                       "actor": OPERATOR, "expected": "CANCELLED", "status": "INTENT_SAVED"}
                report["signed"].append(row)
                report["status"] = "CANCEL_INTENT_SAVED"
                save(report)
                tx_hash = clients[OPERATOR.lower()].write_contract(
                    address=ADDRESS, function_name="cancel_draft", args=[job_id], value=0, leader_only=False
                )
                row.update(hash=str(tx_hash), status="SUBMITTED")
                report["status"] = "CANCEL_SUBMITTED"
                save(report)
                print(json.dumps({"phase": "cancel", "hash": str(tx_hash)}), flush=True)
            elif command == "poll":
                row = report["signed"][-1]
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
                    row.update(status="READBACK_VERIFIED", receipt=tx)
                    if row["phase"] == "create":
                        state = snapshot(job_id)
                        if not state["job"].startswith("DRAFT|") or state["contract_balance"] != 0:
                            raise RuntimeError("CREATE_READBACK_MISMATCH")
                        report["before_simulations"] = state
                        report["status"] = "CREATE_VERIFIED"
                    else:
                        state = snapshot(job_id)
                        if not state["job"].startswith("CANCELLED|") or state["contract_balance"] != 0:
                            raise RuntimeError("CANCEL_READBACK_MISMATCH")
                        report["final_state"] = state
                        report["final_balances"] = {"operator": balance(OPERATOR), "technician": balance(TECHNICIAN),
                                                    "contract": balance(ADDRESS)}
                        report["status"] = "FAILURE_SMOKE_PASSED"
                        public_save(report)
                    save(report)
                    print(json.dumps({"phase": row["phase"], "verified": True, "state": state}), flush=True)
            elif command == "simulate":
                if report["status"] != "CREATE_VERIFIED":
                    raise RuntimeError("SIMULATION_NOT_ALLOWED")
                before = snapshot(job_id)
                cases = [
                    ("wrong-funder", TECHNICIAN, "fund_job", [job_id], BOUNTY, "error", "OPERATOR_ONLY"),
                    ("underfund", OPERATOR, "fund_job", [job_id], BOUNTY - 1, "error", "WRONG_FUNDING_VALUE"),
                    ("overfund", OPERATOR, "fund_job", [job_id], BOUNTY + 1, "error", "WRONG_FUNDING_VALUE"),
                    ("wrong-technician-submit", OPERATOR, "submit_proof", [job_id, MANIFEST_URL, MANIFEST_SHA256], 0,
                     "result", "TECHNICIAN_ONLY"),
                    ("assess-before-proof", OPERATOR, "assess_proof", [job_id], 0, "result", "PROOF_NOT_READY"),
                    ("release-before-authorization", OPERATOR, "execute_release", [job_id], 0,
                     "result", "RELEASE_NOT_AUTHORIZED"),
                    ("refund-before-authorization", OPERATOR, "execute_refund", [job_id], 0,
                     "result", "REFUND_NOT_AUTHORIZED"),
                    ("recover-too-early", TECHNICIAN, "recover_expired", [job_id], 0,
                     "result", "RECOVERY_NOT_ALLOWED"),
                ]
                for name, sender, method, args, value, expected_kind, expected in cases:
                    receipt = simulation_rpc("sim_call", [call_params(sender, method, args, value)])
                    row = {"case": name, "sender": sender, "method": method, "args": args, "value": value,
                           "execution_result": receipt.get("execution_result"), "result": decode_result(receipt),
                           "error": decode_error(receipt), "expected": expected}
                    report["simulations"].append(row)
                    save(report)
                    actual = row[expected_kind]
                    print(json.dumps({"case": name, "execution_result": row["execution_result"],
                                      expected_kind: actual}), flush=True)
                    if actual != expected:
                        raise RuntimeError("FROZEN_SIMULATION_EXPECTATION_MISMATCH")
                after = snapshot(job_id)
                if after != before:
                    raise RuntimeError("SIMULATION_CHANGED_FINAL_STATE")
                report["after_simulations"] = after
                report["status"] = "SIMULATIONS_VERIFIED"
                save(report)
                print("FAILURE_SIMULATIONS_PASSED_STATE_UNCHANGED", flush=True)
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
