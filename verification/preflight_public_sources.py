"""Read-only HTTP/hash check; no image redistribution and no transactions."""
import hashlib
import json
from pathlib import Path
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    registry = json.loads((Path(__file__).parents[1] / "fixtures" / "public-source-registry.json").read_text(encoding="utf-8"))
    opener = urllib.request.build_opener(NoRedirect)
    rows = []
    for image in registry["images"]:
        row = {"url": image["url"], "scope": "development-machine-http-only"}
        try:
            request = urllib.request.Request(image["url"], headers={"User-Agent": "FilterProof-Fixture-Preflight/1.0"})
            with opener.open(request, timeout=20) as response:
                body = response.read(4_000_001)
                digest = hashlib.sha256(body).hexdigest()
                row.update(status=response.status, bytes=len(body), sha256=digest, passed=response.status == 200 and len(body) <= 4_000_000 and digest == image["sha256"])
        except Exception as error:
            row.update(passed=False, error=str(error))
        rows.append(row)
    print(json.dumps({"results": rows, "all_http_hash_checks_passed": all(row["passed"] for row in rows), "live_model_verified": False}, indent=2))
    return 0 if all(row["passed"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
