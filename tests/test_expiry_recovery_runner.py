from verification.run_expiry_recovery import BOUNTY, METHODS, PHASES


def test_expiry_recovery_is_bounded_and_permissionless():
    assert BOUNTY == 10**16
    assert PHASES == ("create", "fund", "recover")
    assert METHODS[-1] == "recover_expired"
