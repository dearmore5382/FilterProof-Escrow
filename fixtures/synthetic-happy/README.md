# Synthetic happy-path fixture

These three AI-generated images depict one fictional system. They are solely a software test fixture and do not document real maintenance.

Sealed test fields:

- Site: `DEMO-SITE-01`
- Asset: `FP-TEST-001`
- Filters: `SED-5M, CARBON-10, UF-01`
- Pressure: `200` kPa before, `300` kPa after
- Files: `before.png`, `after.png`, `serial-gauge.png`

Every image contains `SYNTHETIC TEST FIXTURE` and `NOT A REAL SERVICE`. The generator prompts are preserved in `PROMPTS.md`. `metadata.json` records hashes and generation lineage.

The fixture is a candidate happy path, not a predetermined verdict. A live GenLayer result must be recorded as observed; do not change expected results after seeing consensus. It tests acquisition, byte commitments and semantic workflow, but cannot establish real-image accuracy or physical authenticity.

The three exact image bytes were pinned on 2026-09-03. `pinata-images.json` records their CIDv1 identifiers, immutable gateway URLs, raw-content hashes and a successful download verification. The uploader accepts a scoped `PINATA_JWT` from the environment or one stdin line, uses Pinata's `pinFileToIPFS` endpoint, and never persists the JWT.

After pinning the three exact PNG bytes, create the on-chain manifest only after the real job ID and technician address exist:

```powershell
python build_manifest.py --job-id 0 --technician 0x... --service-date 2026-09-03 `
  --before-url https://.../before.png --after-url https://.../after.png `
  --detail-url https://.../serial-gauge.png
```

Pin the generated `manifest.json` unchanged and submit its printed SHA-256. Do not use Pinata transformations or replace files at mutable URLs.
