from datetime import datetime
from diagnostics.simulate_source import params, ANCHOR


def test_snapshot_params_zero_value_and_explicit_utc():
    result = params(b"control", [], "2026-09-03T10:00:00+00:00")
    assert result["type"] == "deploy" and result["to"] == ANCHOR
    assert result["value"] == "0x0"
    assert datetime.fromisoformat(result["sim_config"]["genvm_datetime"]).tzinfo is not None
    assert "validators" not in result["sim_config"]
