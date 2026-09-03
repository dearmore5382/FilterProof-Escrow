"""One-shot unsigned replay/duplicate-settlement checks on the paid test job."""
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from diagnostics.read_probe import rpc
from diagnostics.run_image_probe import decode_result, decode_error
from diagnostics.run_escrow_preview import ROOT, SOURCE_SHA256, MANIFEST_URL, MANIFEST_SHA256

ADDRESS = "0xf99765498d9F2DF004Ce5B117B78fB5EBb68CD29"
OPERATOR = "0x736A168247e3f0C52F7907c9a8fDac572DF9c8bB"
TECHNICIAN = "0xA63DE24e30C88FB1019E8956654730316e36eDBE"
CASES = (
    ("assessment-replay",OPERATOR,"assess_proof",[0],"PROOF_NOT_READY"),
    ("duplicate-release",OPERATOR,"execute_release",[0],"RELEASE_NOT_AUTHORIZED"),
    ("refund-after-payment",OPERATOR,"execute_refund",[0],"REFUND_NOT_AUTHORIZED"),
    ("late-proof",TECHNICIAN,"submit_proof",[0,MANIFEST_URL,MANIFEST_SHA256],"PROOF_NOT_ALLOWED"),
)


def params(sender,method,args):
    return {"type":"write","to":ADDRESS,"from":sender,"value":"0x0",
            "data":serialize([calldata.encode({"method":method,"args":args}),b'\x00'])}


def view(method,args=None):
    data={"type":"read","to":ADDRESS,"from":OPERATOR,"value":"0x0",
          "transaction_hash_variant":"latest-final",
          "data":serialize([calldata.encode({"method":method,"args":args or []}),b'\x00'])}
    raw=rpc("gen_call",[data])
    return str(calldata.decode(bytes.fromhex(raw.removeprefix("0x"))))


def snapshot():
    return {"counts":view("get_counts"),"job":view("get_job",[0]),
            "attempt":view("get_attempt",[0]),"accounting":view("get_accounting",[0])}


def main():
    source=base64.b64decode(rpc("gen_getContractCode",[ADDRESS]))
    if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256: raise RuntimeError("SOURCE_MISMATCH")
    before=snapshot()
    if not before["job"].startswith("PAID|") or before["accounting"].split("|")[:4] != ["100000000000000000","0","100000000000000000","0"]:
        raise RuntimeError("EXPECTED_PAID_STATE_STOP")
    checkpoint=ROOT/".diagnostic-private"/("postterminal-"+ADDRESS.lower()+".json")
    if checkpoint.exists(): raise RuntimeError("POSTTERMINAL_ALREADY_CHECKPOINTED_STOP")
    report={"contract":ADDRESS,"source_sha256":SOURCE_SHA256,"started_at":datetime.now(timezone.utc).isoformat(),
            "kind":"unsigned leader snapshot simulations; not transactions or consensus evidence",
            "signed_transactions":0,"attached_value":0,"before":before,"cases":[],"status":"INTENT_SAVED"}
    checkpoint.write_text(json.dumps(report,indent=2),encoding="utf-8")
    for name,sender,method,args,expected in CASES:
        receipt=rpc("sim_call",[params(sender,method,args)])
        row={"case":name,"sender":sender,"method":method,"args":args,"expected":expected,
             "execution_result":receipt.get("execution_result"),"result":decode_result(receipt),
             "error":decode_error(receipt),"genvm_result":receipt.get("genvm_result")}
        report["cases"].append(row)
        checkpoint.write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps({k:row[k] for k in ("case","execution_result","result","error")}),flush=True)
        if row["execution_result"]!="SUCCESS" or row["result"]!=expected: raise RuntimeError("FROZEN_EXPECTATION_MISMATCH_STOP")
    report["after"]=snapshot()
    if report["after"]!=before: raise RuntimeError("POSTTERMINAL_STATE_CHANGED")
    report["status"]="POSTTERMINAL_CHECKS_PASSED_NOT_CONSENSUS_PROOF"
    checkpoint.write_text(json.dumps(report,indent=2),encoding="utf-8")
    public={k:v for k,v in report.items() if k!="kind"}
    public["evidence_kind"]=report["kind"]
    output=ROOT/"verification"/("postterminal-"+ADDRESS.lower()+".json")
    output.write_text(json.dumps(public,indent=2)+"\n",encoding="utf-8")
    print("POSTTERMINAL_CHECKS_PASSED_STATE_UNCHANGED",flush=True)


if __name__=="__main__": main()
