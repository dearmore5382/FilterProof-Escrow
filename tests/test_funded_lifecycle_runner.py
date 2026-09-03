import base64
import pytest
from genlayer_py.abi import calldata
from verification.run_funded_lifecycle import action, validate_tx, ADDRESS, OPERATOR, TECHNICIAN, BOUNTY


def test_only_funding_sends_exact_authorized_value():
    steps = [action(i,"2026-09-03T12:00:00Z") for i in range(5)]
    assert sum(s["value"] for s in steps) == BOUNTY
    assert [s["value"] for s in steps] == [0,BOUNTY,0,0,0]
    assert steps[2]["actor"] == TECHNICIAN
    assert all(s["actor"] == OPERATOR for i,s in enumerate(steps) if i!=2)


def test_finality_alone_or_wrong_recipient_never_passes():
    row = dict(action(0,"2026-09-03T12:00:00Z"),hash="0x"+"1"*64)
    tx = {"hash":row["hash"],"status":"FINALIZED","result_name":"MAJORITY_AGREE",
          "from_address":OPERATOR,"to_address":ADDRESS,"value":0,"leader_only":False,
          "data":{"calldata":base64.b64encode(calldata.encode({"method":row["method"],"args":row["args"]})).decode()},
          "consensus_data":{"leader_receipt":[{"mode":"leader","execution_result":"SUCCESS",
                "result":base64.b64encode(b'\x00'+calldata.encode(0)).decode()}]}}
    validate_tx(tx,row)
    for key,value in (("status","ACCEPTED"),("result_name","UNDETERMINED"),("to_address",TECHNICIAN),("value",1),("leader_only",True)):
        with pytest.raises(RuntimeError): validate_tx(dict(tx,**{key:value}),row)
