import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic-happy"


def test_synthetic_fixture_integrity_and_disclosure():
    metadata = json.loads((ROOT / "metadata.json").read_text(encoding="utf-8"))
    pinata = json.loads((ROOT / "pinata-images.json").read_text(encoding="utf-8"))
    assert metadata["real_service_evidence"] is False
    assert metadata["pinata"]["uploaded"] is True
    assert metadata["pinata"]["exact_byte_hashes_verified"] is True
    assert pinata["complete"] is True
    assert metadata["live_genlayer_result"] == "NOT_RUN"
    assert metadata["disclosure_text"] == ["SYNTHETIC TEST FIXTURE", "NOT A REAL SERVICE"]
    assert len(metadata["files"]) == 3
    digests = set()
    for row in metadata["files"]:
        body = (ROOT / row["name"]).read_bytes()
        assert 0 < len(body) <= 4_000_000
        assert body[:8] == b"\x89PNG\r\n\x1a\n"
        digest = hashlib.sha256(body).hexdigest()
        assert digest == row["sha256"]
        public = pinata["files"][row["name"]]
        assert public["content_bytes"] == len(body)
        assert public["sha256"] == digest
        assert public["gateway_verified"] is True
        assert metadata["pinata"]["cids"][row["name"]] == public["cid"]
        assert metadata["pinata"]["gateway_urls"][row["name"]] == public["gateway_url"]
        digests.add(digest)
    assert len(digests) == 3


def test_manifest_builder_uses_exact_contract_schema(tmp_path):
    spec = importlib.util.spec_from_file_location("synthetic_manifest", ROOT / "build_manifest.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.canonical_https("https://gateway.example/ipfs/cid/before.png")
    for value in ("http://gateway.example/a", "https://127.0.0.1/a", "https://gateway.example/a?x=1"):
        assert not module.canonical_https(value)
    source = (ROOT / "build_manifest.py").read_text(encoding="utf-8")
    for field in (
        "schema", "job_id", "site_code", "asset_serial", "technician", "service_date",
        "installed_filters", "pressure_before_kpa", "pressure_after_kpa", "before_image_url",
        "after_image_url", "serial_gauge_image_url", "before_image_sha256", "after_image_sha256",
        "serial_gauge_image_sha256", "notes",
    ):
        assert f'"{field}"' in source
