"""Build exact FilterProof JSON after images are pinned. No upload or transaction."""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parent
def canonical_https(value: str) -> bool:
    if not value.startswith("https://") or any(char in value for char in "?#\\"):
        return False
    rest = value[8:]
    if "/" not in rest:
        return False
    host = rest.split("/", 1)[0].lower()
    return bool(host and "." in host and "@" not in host and ":" not in host and not all(char in "0123456789." for char in host))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True, type=int)
    parser.add_argument("--technician", required=True)
    parser.add_argument("--before-url", required=True)
    parser.add_argument("--after-url", required=True)
    parser.add_argument("--detail-url", required=True)
    parser.add_argument("--before-file", default="before.png")
    parser.add_argument("--after-file", default="after.png")
    parser.add_argument("--detail-file", default="serial-gauge.png")
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--output", default=str(ROOT / "manifest.json"))
    args = parser.parse_args()
    if args.job_id < 0 or not (len(args.technician) == 42 and args.technician.startswith("0x")):
        raise SystemExit("Invalid job ID or technician address")
    urls = [args.before_url, args.after_url, args.detail_url]
    if len(set(urls)) != 3 or not all(canonical_https(url) for url in urls):
        raise SystemExit("Use three distinct canonical HTTPS URLs")
    selected = {
        "before": ROOT / args.before_file,
        "after": ROOT / args.after_file,
        "serial_gauge": ROOT / args.detail_file,
    }
    if any(path.parent != ROOT or not path.is_file() for path in selected.values()):
        raise SystemExit("Image files must exist directly inside the fixture directory")
    digests = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in selected.items()}
    manifest = {
        "schema": "filterproof-service-v1",
        "job_id": str(args.job_id),
        "site_code": "DEMO-SITE-01",
        "asset_serial": "FP-TEST-001",
        "technician": args.technician,
        "service_date": args.service_date,
        "installed_filters": "SED-5M, CARBON-10, UF-01",
        "pressure_before_kpa": 200,
        "pressure_after_kpa": 300,
        "before_image_url": args.before_url,
        "after_image_url": args.after_url,
        "serial_gauge_image_url": args.detail_url,
        "before_image_sha256": digests["before"],
        "after_image_sha256": digests["after"],
        "serial_gauge_image_sha256": digests["serial_gauge"],
        "notes": "SYNTHETIC TEST FIXTURE — NOT A REAL SERVICE. Generated exclusively for happy-path software testing.",
    }
    body = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(body) > 12_000:
        raise SystemExit("Manifest exceeds contract limit")
    output = Path(args.output)
    output.write_bytes(body)
    print(json.dumps({"path": str(output), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
