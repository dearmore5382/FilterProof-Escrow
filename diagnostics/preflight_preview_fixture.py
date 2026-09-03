"""Bounded developer HTTP checks of the already-public original PNG bundle."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import requests
from diagnostics.run_escrow_preview import ROOT, MANIFEST_URL, MANIFEST_SHA256


def fetch(url, digest, limit):
    row = {"url":url,"expected_sha256":digest}
    try:
        with requests.get(url,timeout=20,allow_redirects=False,stream=True) as response:
            response.raw.decode_content = True
            body = response.raw.read(limit+1)
            actual = hashlib.sha256(body).hexdigest()
            row.update(status=response.status_code,bytes=len(body),sha256=actual,
                       passed=response.status_code == 200 and 0 < len(body) <= limit and actual == digest)
    except requests.RequestException as exc:
        row.update(passed=False,error_type=type(exc).__name__)
    return row


def main():
    manifest_bytes = (ROOT / "fixtures/synthetic-happy/manifest.json").read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256:
        raise RuntimeError("LOCAL_FIXTURE_MISMATCH")
    manifest = json.loads(manifest_bytes)
    rows = [fetch(MANIFEST_URL,MANIFEST_SHA256,12000)]
    items = [(manifest[p+"_image_url"],manifest[p+"_image_sha256"],4_000_000)
             for p in ("before","after","serial_gauge")]
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows.extend(pool.map(lambda values:fetch(*values),items))
    report = {"checked_at":datetime.now(timezone.utc).isoformat(),
              "scope":"developer HTTP/hash only; not validator fetch or semantic evidence",
              "fixture":"original disclosed synthetic PNGs; no new upload or image substitution",
              "all_passed":all(row["passed"] for row in rows),"results":rows}
    output = ROOT / "verification/preview-fixture-preflight.json"
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if not report["all_passed"]: raise SystemExit(2)


if __name__ == "__main__":
    main()
