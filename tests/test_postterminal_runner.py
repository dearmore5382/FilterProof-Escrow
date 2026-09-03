from verification.run_funded_lifecycle import ADDRESS, OPERATOR, TECHNICIAN
from diagnostics.run_postterminal_checks import CASES, params


def test_postterminal_matrix_is_zero_value_and_scoped():
    assert [c[0] for c in CASES] == ["assessment-replay","duplicate-release","refund-after-payment","late-proof"]
    assert [c[4] for c in CASES] == ["PROOF_NOT_READY","RELEASE_NOT_AUTHORIZED","REFUND_NOT_AUTHORIZED","PROOF_NOT_ALLOWED"]
    for _,sender,method,args,_ in CASES:
        value=params(sender,method,args)
        assert value["to"]==ADDRESS and value["value"]=="0x0" and value["type"]=="write"
    assert CASES[-1][1]==TECHNICIAN and all(c[1]==OPERATOR for c in CASES[:-1])
