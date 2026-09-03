"""Run the disclosed synthetic happy-path candidate on an existing Studionet deployment.

Private keys are requested with getpass and are never written to disk. Public
transaction receipts and finalized readbacks are checkpointed after every write.
"""
import argparse
import getpass
import json
import time
from pathlib import Path

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet


ROOT = Path(__file__).resolve().parent
GEN = 10**18
BOUNTY = GEN // 10
TITLE = "Synthetic commercial filter replacement"
SITE = "DEMO-SITE-01"
SERIAL = "FP-TEST-001"
FILTERS = "SED-5M, CARBON-10, UF-01"
RECOVERY_AFTER = "2030-01-01T00:00:00Z"


def readable(value):
    if isinstance(value, dict):
        payload = value.get("payload")
        if isinstance(payload, dict) and "readable" in payload:
            return str(payload["readable"])
        for child in value.values():
            found = readable(child)
            if found is not None:
                return found
    if isinstance(value, list):
        for child in value:
            found = readable(child)
            if found is not None:
                return found
    return None


def normalized_result(receipt):
    result = readable(receipt)
    if isinstance(result, str):
        try:
            decoded = json.loads(result)
            if isinstance(decoded, (str, int)):
                return str(decoded)
        except json.JSONDecodeError:
            pass
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("bootstrap", "settle", "refund"))
    parser.add_argument("--contract", required=True)
    parser.add_argument("--manifest-url")
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args()
    if args.phase == "settle" and (not args.manifest_url or not args.manifest_sha256):
        parser.error("settle requires --manifest-url and --manifest-sha256")
    log = ROOT / f"live-happy-{args.contract.lower()}.json"

    operator_key = getpass.getpass("")
    technician_key = getpass.getpass("")
    operator = create_account(account_private_key="0x" + operator_key.removeprefix("0x"))
    technician = create_account(account_private_key="0x" + technician_key.removeprefix("0x"))
    operator_client = create_client(chain=studionet, account=operator)
    technician_client = create_client(chain=studionet, account=technician)
    records = json.loads(log.read_text(encoding="utf-8")) if log.exists() else []

    def save(row):
        records.append(row)
        log.write_text(json.dumps(records, indent=2, default=str) + "\n", encoding="utf-8")

    def view(method, call_args=None):
        value = operator_client.read_contract(
            address=args.contract, function_name=method, args=call_args or []
        )
        text = str(value)
        print(f"READ {method}{call_args or []} -> {text}", flush=True)
        return text

    def write(case, client, actor, method, call_args, expected=None, value=0):
        tx_hash = client.write_contract(
            address=args.contract,
            function_name=method,
            args=call_args,
            value=value,
        )
        print(f"{case} {method} tx={tx_hash}", flush=True)
        receipt = None
        for _ in range(240):
            current = operator_client.get_transaction(tx_hash)
            if current.get("status_name") == "FINALIZED":
                receipt = current
                break
            time.sleep(5)
        if receipt is None:
            raise TimeoutError(f"{case}: transaction did not finalize")
        result = normalized_result(receipt)
        row = {
            "case": case,
            "actor": actor,
            "method": method,
            "args": call_args,
            "value": str(value),
            "transaction": str(tx_hash),
            "status": receipt.get("status_name"),
            "consensus_result": receipt.get("result_name"),
            "return": result,
            "receipt": json.loads(json.dumps(receipt, default=str)),
        }
        save(row)
        print(
            f"{case} FINALIZED consensus={row['consensus_result']} return={result}",
            flush=True,
        )
        if row["consensus_result"] != "MAJORITY_AGREE":
            raise AssertionError(f"{case}: state was not committed by majority consensus")
        if expected is not None and result != expected:
            raise AssertionError(f"{case}: expected {expected!r}, got {result!r}")
        return result

    print(f"contract={args.contract}", flush=True)
    print(f"operator={operator.address}", flush=True)
    print(f"technician={technician.address}", flush=True)

    if args.phase == "refund":
        if view("get_counts") != "1|2" or not view("get_job", [0]).startswith("REFUND_AUTHORIZED|"):
            raise AssertionError("refund requires job 0 in REFUND_AUTHORIZED after two attempts")
        balance_before = operator_client.get_balance(operator.address)
        write("H2-03", operator_client, operator.address, "execute_refund", [0], "REFUNDED")
        final_job = view("get_job", [0])
        final_accounting = view("get_accounting", [0])
        balance_after = operator_client.get_balance(operator.address)
        triggered = operator_client.get_triggered_transaction_ids(records[-1]["transaction"])
        save({
            "case": "H2-FINAL",
            "job": final_job,
            "accounting": final_accounting,
            "operator_balance_before": str(balance_before),
            "operator_balance_after": str(balance_after),
            "triggered_transactions": triggered,
        })
        if not final_job.startswith("REFUNDED|"):
            raise AssertionError("refund did not reach REFUNDED")
        parts = final_accounting.split("|")
        if parts[:4] != [str(BOUNTY), "0", "0", str(BOUNTY)]:
            raise AssertionError("refund accounting mismatch")
        print("REFUND_COMPLETE", flush=True)
        return

    if args.phase == "bootstrap":
        if view("get_counts") != "0|0":
            raise AssertionError("bootstrap requires a fresh 0|0 deployment")
        write(
            "H1-01",
            operator_client,
            operator.address,
            "create_job",
            [TITLE, SITE, SERIAL, FILTERS, technician.address, BOUNTY, RECOVERY_AFTER],
            "0",
        )
        sealed = view("get_job", [0])
        expected = "|".join(
            ["DRAFT", operator.address, technician.address, TITLE, SITE, SERIAL, FILTERS, RECOVERY_AFTER, "0"]
        )
        if sealed.lower() != expected.lower():
            raise AssertionError("sealed job readback mismatch")
        write("H1-02", operator_client, operator.address, "fund_job", [0], "FUNDED", BOUNTY)
        if not view("get_job", [0]).startswith("FUNDED|"):
            raise AssertionError("funded state readback mismatch")
        print("BOOTSTRAP_COMPLETE", flush=True)
        return

    counts = view("get_counts")
    job_before = view("get_job", [0])
    if counts == "1|0" and job_before.startswith("FUNDED|"):
        submit_case = "H1-03"
        expected_attempt = "0"
    elif counts == "1|1" and job_before.startswith("CORRECTION_REQUIRED|"):
        submit_case = "H2-01"
        expected_attempt = "1"
    else:
        raise AssertionError(
            "settle requires a fresh FUNDED job or exactly one CORRECTION_REQUIRED attempt"
        )
    write(
        submit_case,
        technician_client,
        technician.address,
        "submit_proof",
        [0, args.manifest_url, args.manifest_sha256],
        expected_attempt,
    )
    assessment_case = "H1-04" if expected_attempt == "0" else "H2-02"
    assessment = write(assessment_case, operator_client, operator.address, "assess_proof", [0])
    attempt = view("get_attempt", [int(expected_attempt)])
    job = view("get_job", [0])
    accounting = view("get_accounting", [0])
    save({"case": "H1-READBACK", "attempt": attempt, "job": job, "accounting": accounting})
    if assessment == "RELEASE_AUTHORIZED":
        release_case = "H1-05" if expected_attempt == "0" else "H2-03"
        write(release_case, operator_client, operator.address, "execute_release", [0], "PAID")
        final_job = view("get_job", [0])
        final_accounting = view("get_accounting", [0])
        save({"case": "H1-FINAL", "job": final_job, "accounting": final_accounting})
        if not final_job.startswith("PAID|"):
            raise AssertionError("release did not reach PAID")
    else:
        print(f"OBSERVED_NON_RELEASE={assessment}", flush=True)
    print("SETTLE_PHASE_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
