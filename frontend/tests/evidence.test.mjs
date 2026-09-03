import test from 'node:test';
import assert from 'node:assert/strict';
import { canonicalHttps, validateManifest } from '../lib/evidence.mjs';
const fixture = {
  schema: 'filterproof-service-v1',
  job_id: '0',
  site_code: 'SITE',
  asset_serial: 'SERIAL',
  technician: '0x' + '1'.repeat(40),
  service_date: '2026-09-03',
  installed_filters: 'SED, CARBON',
  pressure_before_kpa: 200,
  pressure_after_kpa: 300,
  notes: '',
  before_image_url: 'https://proof.example/b.jpg',
  after_image_url: 'https://proof.example/a.jpg',
  serial_gauge_image_url: 'https://proof.example/s.jpg',
  before_image_sha256: 'a'.repeat(64),
  after_image_sha256: 'b'.repeat(64),
  serial_gauge_image_sha256: 'c'.repeat(64),
};
test('manifest matches exact contract field set', () => {
  const text = validateManifest(fixture);
  assert.equal(Object.keys(JSON.parse(text)).length, 16);
  assert.throws(() => validateManifest({ ...fixture, payment: 'APPROVE' }));
});
test('adversarial URL variants fail closed', () => {
  assert.equal(canonicalHttps('https://proof.example/a.jpg'), true);
  for (const u of [
    'http://proof.example/a',
    'https://127.0.0.1/a',
    'https://x.localhost/a',
    'https://proof.example:443/a',
    'https://user@proof.example/a',
    'https://proof.example/a?x=1',
    'https://proof.example/a\n',
    'https://-bad.example/a',
  ])
    assert.equal(canonicalHttps(u), false, u);
});
test('duplicate image, pressure coercion, impossible dates, delimiter rejected', () => {
  for (const change of [
    { after_image_sha256: fixture.before_image_sha256 },
    { pressure_before_kpa: 1.5 },
    { pressure_after_kpa: true },
    { service_date: '2026-02-30' },
    { installed_filters: 'A|B' },
  ])
    assert.throws(() => validateManifest({ ...fixture, ...change }));
});
