# Synthetic happy-path image prompts

Generator: built-in ImageGen. Purpose: software test fixture, not evidence of an actual maintenance event. Requested by the user on 2026-09-03.

## Shared invariants

Square 1024x1024 training render. Fictional commercial three-stage filter rack, grey stainless frame against a light grey utility wall, blue top manifold, three clear filter housings in a single row. No real manufacturer logos, people, customer data or geographic claims.

Visible identifiers: `SITE: DEMO-SITE-01`, `ASSET: FP-TEST-001`.
Left to right filter labels: `SED-5M`, `CARBON-10`, `UF-01`.
Every image must carry `SYNTHETIC TEST FIXTURE` and `NOT A REAL SERVICE`.
No approval, payout, PASS, verdict or instructions directed at validators in the images.

## 01 — Before

Create an educational, high-detail realistic 3D training render of this fictional rack before maintenance. Front-on full rack view with readable identity plate and cartridge labels. Three old cartridges are visible through clear housings: lightly brown stained pleated sediment element, used black carbon element, and off-white UF element. Single clearly readable digital outlet gauge above the manifold reads `200 kPa`. All pipe connections are coherent. Top title `BEFORE MAINTENANCE`. Bottom safety banner `SYNTHETIC TEST FIXTURE` / `NOT A REAL SERVICE`. Neutral even light; all evidence readable. Exactly three installed housings. No extra unit or gauge, no real logo, no service completion claims. Square 1024x1024.

## 02 — After

Use image 01 as the structural identity reference. Preserve the same rack, mounting points, manifold, pipe connections, identity plate, camera framing and lighting. Replace only the contents of all three clear housings with clean new cartridges: white pleated sediment, new black carbon, clean white UF. Preserve exact labels `SED-5M`, `CARBON-10`, `UF-01`. The digital outlet gauge now reads `300 kPa`. Three removed old cartridges sit on a shallow tray below, corresponding to the before image, and three empty generic sleeves beside the tray display the same cartridge codes. Top title `AFTER REPLACEMENT`. Keep both synthetic safety labels. No PASS/approval/payment text. Square 1024x1024.

## 03 — Identity and gauge detail

Use image 02 as the reference. Make a closer view of the same asset identity plate, the digital outlet gauge reading `300 kPa` and the upper portions of the same three labeled filter housings. Preserve all identifiers and exact hardware layout. It must be recognizably the same rack, not a different unit. Top title `IDENTITY & GAUGE DETAIL`. Keep both synthetic safety labels clearly legible. No invented extra numbers, real-world brands, completion claims, PASS/approval/payment text. Square 1024x1024.

## Actual generation method

- `before.png`: generated from prompt 01 with no input image.
- `after.png`: precise-object edit using `before.png` as the reference.
- `serial-gauge.png`: precise-object edit using `after.png` as the reference.
- Generated with the built-in ImageGen tool. ImageGen does not provide a reproducible random seed; byte hashes in `metadata.json` are the immutable identity of these outputs.
