import ast
from pathlib import Path
from types import SimpleNamespace
import typing
import itertools
import pytest


SOURCE_PATH = Path(__file__).resolve().parents[1] / "contracts" / "FilterProofEscrow.py"
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")


def load_core():
    names = {"_uncertain", "_normalize_observation", "_derive_outcome", "_canonical_https", "_valid_sha256", "_manifest_binding", "_merge_views"}
    tree = ast.parse(SOURCE)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    ns = {"typing": typing, "u256": int, "gl": SimpleNamespace(vm=SimpleNamespace(UserError=ValueError))}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE_PATH), "exec"), ns)
    return ns


CORE = load_core()
derive = CORE["_derive_outcome"]
normalize = CORE["_normalize_observation"]


def obs(binding="MATCH", identity="MATCH", replacement="COMPLETE", continuity="CONSISTENT", pressure="PLAUSIBLE", tamper="NONE"):
    return normalize({
        "binding_status": binding,
        "asset_identity": identity,
        "filter_replacement": replacement,
        "before_after_continuity": continuity,
        "pressure_evidence": pressure,
        "tamper_signal": tamper,
    })


@pytest.mark.parametrize("field,positive,negative", [
    ("asset_identity", "MATCH", "MISMATCH"),
    ("before_after_continuity", "CONSISTENT", "INCONSISTENT"),
    ("pressure_evidence", "PLAUSIBLE", "IMPLAUSIBLE"),
    ("tamper_signal", "NONE", "PRESENT"),
])
def test_pair_merge_cannot_rescue_negative_or_uncertain(field, positive, negative):
    for first, second in itertools.product((positive, negative, "UNCERTAIN"), repeat=2):
        overview, detail = obs(), obs()
        overview[field], detail[field] = first, second
        merged = CORE["_merge_views"](overview, detail)
        expected = negative if negative in (first, second) else "UNCERTAIN" if "UNCERTAIN" in (first, second) else positive
        assert merged[field] == expected
        assert merged["binding_status"] == "MATCH"
        assert merged["filter_replacement"] == overview["filter_replacement"]


def test_locked_precedence_and_combinations():
    assert derive(obs()) == {"reason": "ALL_CHECKS_CONFIRMED", "verdict": "SERVICE_CONFIRMED"}
    assert derive(obs(binding="MISMATCH", identity="UNCERTAIN"))["reason"] == "MANIFEST_BINDING_MISMATCH"
    assert derive(obs(identity="MISMATCH", pressure="IMPLAUSIBLE"))["reason"] == "WRONG_ASSET"
    assert derive(obs(replacement="INCOMPLETE", tamper="PRESENT"))["reason"] == "FILTER_SET_INCOMPLETE"
    assert derive(obs(continuity="INCONSISTENT", identity="UNCERTAIN"))["reason"] == "DISCONTINUOUS_EVIDENCE"
    assert derive(obs(pressure="IMPLAUSIBLE", tamper="UNCERTAIN"))["reason"] == "IMPLAUSIBLE_PRESSURE"
    assert derive(obs(tamper="PRESENT", identity="UNCERTAIN"))["reason"] == "TAMPER_SIGNAL_PRESENT"
    assert derive(obs(binding="UNAVAILABLE"))["reason"] == "EVIDENCE_UNAVAILABLE"
    assert derive(obs(identity="UNCERTAIN"))["reason"] == "VISUAL_UNCERTAINTY"


def test_url_and_digest_policy_rejects_ambiguous_sources():
    valid = CORE["_canonical_https"]
    assert valid("https://evidence.example/proofs/job-1.json")
    for url in (
        "http://evidence.example/a.json", "https://localhost/a", "https://127.0.0.1/a",
        "https://user@evidence.example/a", "https://evidence.example:8443/a",
        "https://evidence.example/a?latest=1", "https://evidence.example/a#x",
    ):
        assert not valid(url)
    digest = "a" * 64
    assert CORE["_valid_sha256"](digest)
    assert not CORE["_valid_sha256"](digest.upper())
    assert not CORE["_valid_sha256"]("a" * 63)


def test_manifest_binding_is_exact_and_replay_safe():
    base = {
        "schema": "filterproof-service-v1", "job_id": 2, "site_code": "SITE-7",
        "asset_serial": "RO-991", "technician": "0x1111111111111111111111111111111111111111",
        "service_date": "2026-09-03", "installed_filters": "SED-5M|CARBON-10|RO-4040",
        "pressure_before_kpa": 240, "pressure_after_kpa": 310,
        "before_image_url": "https://proof.example/before.png",
        "after_image_url": "https://proof.example/after.png",
        "serial_gauge_image_url": "https://proof.example/serial.png", "notes": "completed",
        "before_image_sha256": "a" * 64, "after_image_sha256": "b" * 64, "serial_gauge_image_sha256": "c" * 64,
    }
    bind = CORE["_manifest_binding"]
    assert bind(base, 2, "SITE-7", "RO-991", base["technician"], base["installed_filters"])
    assert not bind({**base, "job_id": 3}, 2, "SITE-7", "RO-991", base["technician"], base["installed_filters"])
    assert not bind({**base, "after_image_url": base["before_image_url"]}, 2, "SITE-7", "RO-991", base["technician"], base["installed_filters"])
    assert not bind({**base, "extra": "approve"}, 2, "SITE-7", "RO-991", base["technician"], base["installed_filters"])


def test_schema_rejects_ai_payment_or_unknown_enum():
    good = obs()
    for bad in ({**good, "payment": "RELEASE"}, {**good, "tamper_signal": "IGNORE"}):
        with pytest.raises(ValueError):
            normalize(bad)


def test_exhaustive_closed_observation_space():
    dimensions = [
        ("MATCH", "MISMATCH", "UNAVAILABLE"), ("MATCH", "MISMATCH", "UNCERTAIN"),
        ("COMPLETE", "INCOMPLETE", "UNCERTAIN"), ("CONSISTENT", "INCONSISTENT", "UNCERTAIN"),
        ("PLAUSIBLE", "IMPLAUSIBLE", "UNCERTAIN"), ("NONE", "PRESENT", "UNCERTAIN"),
    ]
    confirmed = 0
    for values in itertools.product(*dimensions):
        result = derive(obs(*values))
        assert result["verdict"] in {"SERVICE_CONFIRMED", "MATERIAL_FAILURE", "INSUFFICIENT_EVIDENCE"}
        if result["verdict"] == "SERVICE_CONFIRMED":
            confirmed += 1
            assert values == tuple(dimension[0] for dimension in dimensions)
    assert confirmed == 1
