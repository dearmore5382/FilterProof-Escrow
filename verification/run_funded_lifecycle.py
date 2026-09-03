"""Interactive, checkpointed five-write testnet lifecycle; keys live in memory only.

First stdin line: JSON array of the two authorized test-wallet keys. Subsequent
lines: create/fund/submit/assess/release, poll, payout, or quit. No automatic
resubmission, extra jobs, correction attempts, upgrades or deployments.
"""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import getpass
import json
from pathlib import Path
import sys
import requests
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.abi import calldata
from diagnostics.read_probe import redact
from diagnostics.run_image_probe import call_params
from diagnostics.run_escrow_preview import SOURCE_SHA256, MANIFEST_URL, MANIFEST_SHA256

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29"
OPERATOR = "0x736A168247e3f0C52F7907c9a8fDac572DF9c8bB"
TECHNICIAN = "0xA63DE24e30C88FB1019E8956654730316e36eDBE"
RPC = "https://studio.genlayer.com/api"
BOUNTY = 100_000_000_000_000_000
PHASES = ("create", "fund", "submit", "assess", "release")
METHODS = ("create_job", "fund_job", "submit_proof", "assess_proof", "execute_release")
EXPECTED = ("0", "FUNDED", "0", "RELEASE_AUTHORIZED", "PAID")
STATES = ("DRAFT", "FUNDED", "PROOF_READY", "RELEASE_AUTHORIZED", "PAID")
JOURNAL = ROOT / ".diagnostic-private" / ("funded-lifecycle-"+ADDRESS.lower()+".json")


def rpc(method, params):
    if method not in {"eth_chainId","eth_getBalance","eth_getTransactionByHash","gen_getContractCode","gen_call"}:
        raise ValueError("Read-only RPC allowlist")
    res = requests.post(RPC,json={"jsonrpc":"2.0","id":1,"method":method,"params":params},timeout=25)
    res.raise_for_status()
    data = res.json()
    if "error" in data: raise RuntimeError("RPC_ERROR_"+str(data["error"].get("code")))
    return redact(data["result"])


def view(method, args=None):
    params = call_params(ADDRESS,"read",method,args or [])
    params["transaction_hash_variant"] = "latest-final"
    value = rpc("gen_call",[params])
    return str(calldata.decode(bytes.fromhex(value.removeprefix("0x"))))


def balance(address):
    return int(rpc("eth_getBalance",[address,"latest"]),16)


def parity():
    if int(rpc("eth_chainId",[]),16) != 61999: raise RuntimeError("WRONG_CHAIN")
    if hashlib.sha256(base64.b64decode(rpc("gen_getContractCode",[ADDRESS]))).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("SOURCE_MISMATCH")


def action(index, recovery):
    args = [["Synthetic commercial filter replacement","DEMO-SITE-01","FP-TEST-001",
             "SED-5M, CARBON-10, UF-01",TECHNICIAN,BOUNTY,recovery], [0],
            [0,MANIFEST_URL,MANIFEST_SHA256], [0], [0]][index]
    return {"phase":PHASES[index],"method":METHODS[index],"args":args,
            "actor":TECHNICIAN if index == 2 else OPERATOR,"value":BOUNTY if index == 1 else 0,
            "expected":EXPECTED[index]}


def validate_tx(tx, row):
    if tx.get("status") != "FINALIZED" or tx.get("result_name") != "MAJORITY_AGREE":
        raise RuntimeError("FINALITY_OR_CONSENSUS_NOT_PASSED")
    if str(tx.get("hash")).lower() != row["hash"].lower(): raise RuntimeError("HASH_MISMATCH")
    if str(tx.get("from_address")).lower() != row["actor"].lower() or str(tx.get("to_address")).lower() != ADDRESS.lower():
        raise RuntimeError("TX_PARTY_MISMATCH")
    if int(tx.get("value",-1)) != row["value"] or tx.get("leader_only") is not False:
        raise RuntimeError("VALUE_OR_CONSENSUS_MODE_MISMATCH")
    decoded = calldata.decode(base64.b64decode(tx["data"]["calldata"]))
    if decoded != {"method":row["method"],"args":row["args"]}: raise RuntimeError("CALLDATA_MISMATCH")
    leaders = (tx.get("consensus_data") or {}).get("leader_receipt") or []
    if isinstance(leaders,dict): leaders = [leaders]
    leaders = [x for x in leaders if x.get("mode") == "leader"]
    if not leaders or leaders[-1].get("execution_result") != "SUCCESS": raise RuntimeError("LEADER_FAILED")
    result = leaders[-1]["result"]
    raw = base64.b64decode(result["raw"] if isinstance(result,dict) else result)
    if not raw or raw[0] != 0 or str(calldata.decode(raw[1:])) != row["expected"]:
        raise RuntimeError("UNEXPECTED_CONTRACT_RETURN")


def validate_state(index, snapshot, recovery):
    wanted_counts = "1|0" if index < 2 else "1|1"
    if snapshot["counts"] != wanted_counts: raise RuntimeError("COUNTS_MISMATCH")
    expected_job = [STATES[index],OPERATOR,TECHNICIAN,"Synthetic commercial filter replacement",
                    "DEMO-SITE-01","FP-TEST-001","SED-5M, CARBON-10, UF-01",recovery,"0" if index < 2 else "1"]
    parts = snapshot["job"].split("|")
    if len(parts) != len(expected_job) or any(a.lower()!=b.lower() if i in (1,2) else a!=b for i,(a,b) in enumerate(zip(parts,expected_job))):
        raise RuntimeError("SEALED_JOB_STATE_MISMATCH")
    wanted_accounting = [str(BOUNTY),str(BOUNTY) if 1<=index<=3 else "0",str(BOUNTY) if index==4 else "0","0"]
    if snapshot["accounting"].split("|")[:4] != wanted_accounting: raise RuntimeError("ACCOUNTING_MISMATCH")
    if index >= 2:
        attempt = snapshot["attempt"].split("|")
        expected = ["READY" if index==2 else "ASSESSED","0","1",
                    "UNEVALUATED" if index==2 else "SERVICE_CONFIRMED",
                    "PENDING" if index==2 else "ALL_CHECKS_CONFIRMED",MANIFEST_SHA256]
        if attempt[:6] != expected or attempt[-1] != MANIFEST_URL: raise RuntimeError("ATTEMPT_MISMATCH")


def main():
    if not sys.stdin.isatty(): raise RuntimeError("INTERACTIVE_NO_ECHO_TERMINAL_REQUIRED")
    keys = json.loads(getpass.getpass("KEY_INPUT_REQUIRED_NO_ECHO: "))
    accounts = [create_account(account_private_key="0x"+k.removeprefix("0x")) for k in keys]
    del keys
    clients = {a.address.lower():create_client(chain=studionet,account=a) for a in accounts}
    if set(clients) != {OPERATOR.lower(),TECHNICIAN.lower()}: raise RuntimeError("AUTHORIZED_WALLET_MISMATCH")
    parity()
    initial = {"operator":balance(OPERATOR),"technician":balance(TECHNICIAN),"contract":balance(ADDRESS)}
    if JOURNAL.exists():
        journal = json.loads(JOURNAL.read_text())
        if journal["source_sha256"] != SOURCE_SHA256: raise RuntimeError("JOURNAL_SOURCE_MISMATCH")
    else:
        if view("get_counts") != "0|0" or initial["contract"] != 0: raise RuntimeError("NOT_FRESH")
        if initial["operator"] < BOUNTY: raise RuntimeError("INSUFFICIENT_TEST_BALANCE")
        journal = {"contract":ADDRESS,"source_sha256":SOURCE_SHA256,"chain_id":61999,
                   "authorized_bounty":BOUNTY,"recovery_after":(datetime.now(timezone.utc)+timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "initial_balances":initial,"steps":[],"authorization":"User approved one 0.1 GEN testnet create/fund/submit/assess/release lifecycle"}
    def save():
        JOURNAL.parent.mkdir(exist_ok=True)
        JOURNAL.write_text(json.dumps(journal,indent=2,default=str),encoding="utf-8")
    save()
    print(json.dumps({"ready":True,"wallets":[OPERATOR,TECHNICIAN],"balances":initial,"recovery_after":journal["recovery_after"],"steps":len(journal["steps"])}),flush=True)
    for line in sys.stdin:
        command = line.strip()
        if command == "quit": return
        try:
            if command in PHASES:
                index = len(journal["steps"])
                if index >= 5 or command != PHASES[index]: raise RuntimeError("OUT_OF_ORDER_OR_ALREADY_SENT")
                if index and journal["steps"][-1]["status"] != "READBACK_VERIFIED": raise RuntimeError("PRIOR_WRITE_UNRESOLVED")
                parity()
                if index:
                    current = {"counts":view("get_counts"),"job":view("get_job",[0]),"accounting":view("get_accounting",[0])}
                    if index > 2: current["attempt"] = view("get_attempt",[0])
                    validate_state(index-1,current,journal["recovery_after"])
                elif view("get_counts") != "0|0": raise RuntimeError("CREATE_NOT_FRESH")
                row = action(index,journal["recovery_after"])
                if index == 4: journal["technician_before_release"] = balance(TECHNICIAN)
                row.update(status="INTENT_SAVED",submitted_at=datetime.now(timezone.utc).isoformat())
                journal["steps"].append(row)
                save()
                tx_hash = clients[row["actor"].lower()].write_contract(address=ADDRESS,function_name=row["method"],args=row["args"],value=row["value"],leader_only=False)
                row.update(hash=str(tx_hash),status="SUBMITTED")
                save()
                print(json.dumps({"phase":command,"hash":row["hash"],"status":row["status"]}),flush=True)
            elif command == "poll":
                row = journal["steps"][-1]
                if not row.get("hash"): raise RuntimeError("UNKNOWN_SUBMISSION_DO_NOT_RESEND")
                tx = rpc("eth_getTransactionByHash",[row["hash"]])
                if not tx: raise RuntimeError("TX_NOT_FOUND_KEEP_HASH")
                row["receipt"] = tx
                save()
                print(json.dumps({"phase":row["phase"],"hash":row["hash"],"status":tx.get("status"),"consensus":tx.get("result_name")}),flush=True)
                if tx.get("status") == "FINALIZED":
                    validate_tx(tx,row)
                    snapshot = {"counts":view("get_counts"),"job":view("get_job",[0]),"accounting":view("get_accounting",[0])}
                    if row["phase"] in PHASES[2:]: snapshot["attempt"] = view("get_attempt",[0])
                    row["readback"] = snapshot
                    save()
                    validate_state(PHASES.index(row["phase"]),snapshot,journal["recovery_after"])
                    row["status"] = "READBACK_VERIFIED"
                    save()
                    print(json.dumps({"phase":row["phase"],"verified":True,"readback":snapshot}),flush=True)
            elif command == "payout":
                if len(journal["steps"]) != 5 or journal["steps"][-1]["status"] != "READBACK_VERIFIED": raise RuntimeError("RELEASE_NOT_VERIFIED")
                parent = rpc("eth_getTransactionByHash",[journal["steps"][-1]["hash"]])
                children = parent.get("triggered_transactions") or []
                if not children: raise RuntimeError("CHILD_TRANSFER_NOT_YET_VISIBLE")
                transfers = [rpc("eth_getTransactionByHash",[tx]) for tx in children]
                journal["child_receipts"] = transfers
                journal["technician_after_release"] = balance(TECHNICIAN)
                journal["final_contract_balance"] = balance(ADDRESS)
                save()
                matching = [t for t in transfers if t and t.get("status")=="FINALIZED" and t.get("type")==0
                            and str(t.get("from_address")).lower()==ADDRESS.lower()
                            and str(t.get("to_address")).lower()==TECHNICIAN.lower()
                            and t.get("triggered_by")==parent["hash"] and int(t.get("value",-1))==BOUNTY]
                if len(matching)!=1 or len(transfers)!=1: raise RuntimeError("CHILD_TRANSFER_NOT_VERIFIED")
                if journal["technician_after_release"]-journal["technician_before_release"] != BOUNTY or journal["final_contract_balance"]!=0:
                    raise RuntimeError("BALANCE_EFFECT_NOT_VERIFIED")
                journal["happy_path_verified"] = True
                save()
                print(json.dumps({"happy_path_verified":True,"child":matching[0]["hash"],"technician_received":BOUNTY,"contract_balance":0}),flush=True)
            else:
                raise ValueError("Unknown action")
        except Exception as exc:
            # Never dump SDK exception details containing request/config secrets.
            print(json.dumps({"action_failed":command,"error_type":type(exc).__name__,"journal_preserved":True}),flush=True)
        print("READY_FOR_ACTION",flush=True)


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(json.dumps({"fatal_error_type":type(exc).__name__}),flush=True)
        raise SystemExit(1)
