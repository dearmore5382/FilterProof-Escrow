from verification.run_failure_smoke import BOUNTY, ADDRESS, OPERATOR, TECHNICIAN, call_params


def test_failure_smoke_is_low_value_and_scoped():
    assert BOUNTY == 10**16
    assert ADDRESS.lower() not in {OPERATOR.lower(), TECHNICIAN.lower()}
    payload = call_params(OPERATOR, "fund_job", [1], BOUNTY - 1)
    assert payload["value"] == hex(BOUNTY - 1)
    assert payload["from"] == OPERATOR
