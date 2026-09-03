from verification.run_refund_path import BOUNTY, EXPECTED, PHASES, WRONG_DIGEST


def test_refund_path_is_bounded_and_deterministic():
    assert BOUNTY == 10**16
    assert len(PHASES) == 7
    assert PHASES[-1] == "refund"
    assert EXPECTED[-1] == "REFUNDED"
    assert WRONG_DIGEST == "0" * 64
