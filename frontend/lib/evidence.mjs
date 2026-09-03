import { addressOK, uint } from './protocol.mjs';
export function canonicalHttps(value) {
  if (
    typeof value !== 'string' ||
    value.length > 500 ||
    !/^[\x21-\x7e]+$/.test(value) ||
    !value.startsWith('https://') ||
    /[?#\\]/.test(value)
  )
    return false;
  const host = value.slice(8).split('/')[0].toLowerCase();
  if (
    !value.slice(8).includes('/') ||
    !host.includes('.') ||
    /^[\d.]+$/.test(host) ||
    host.endsWith('.localhost')
  )
    return false;
  return host
    .split('.')
    .every((label) => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label));
}
export function validateManifest(proof) {
  const expected = [
    'schema',
    'job_id',
    'site_code',
    'asset_serial',
    'technician',
    'service_date',
    'installed_filters',
    'pressure_before_kpa',
    'pressure_after_kpa',
    'notes',
    'before_image_url',
    'after_image_url',
    'serial_gauge_image_url',
    'before_image_sha256',
    'after_image_sha256',
    'serial_gauge_image_sha256',
  ];
  if (
    Object.keys(proof).sort().join(',') !== expected.sort().join(',') ||
    proof.schema !== 'filterproof-service-v1'
  )
    throw new Error('Invalid manifest schema.');
  uint(proof.job_id);
  if (!addressOK(proof.technician))
    throw new Error('Enter a valid technician wallet.');
  for (const [field, max] of [
    ['site_code', 80],
    ['asset_serial', 100],
    ['installed_filters', 500],
  ]) {
    if (
      typeof proof[field] !== 'string' ||
      !proof[field].trim() ||
      proof[field].length > max ||
      proof[field].includes('|') ||
      proof[field].includes(String.fromCharCode(0))
    )
      throw new Error('Invalid sealed field: ' + field);
  }
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(proof.service_date) ||
    new Date(proof.service_date + 'T00:00:00Z').toISOString().slice(0, 10) !==
      proof.service_date
  )
    throw new Error('Enter a valid service date.');
  for (const field of ['pressure_before_kpa', 'pressure_after_kpa'])
    if (
      !Number.isInteger(proof[field]) ||
      proof[field] < 0 ||
      proof[field] > 5000
    )
      throw new Error('Pressure must be an integer between 0 and 5000 kPa.');
  const keys = ['before', 'after', 'serial_gauge'];
  const urls = keys.map((key) => proof[key + '_image_url']),
    hashes = keys.map((key) => proof[key + '_image_sha256']);
  if (!urls.every(canonicalHttps) || new Set(urls).size !== 3)
    throw new Error('Use three distinct canonical HTTPS image URLs.');
  if (
    !hashes.every((h) => typeof h === 'string' && /^[a-f0-9]{64}$/.test(h)) ||
    new Set(hashes).size !== 3
  )
    throw new Error('Use three distinct original image files.');
  if (typeof proof.notes !== 'string' || proof.notes.length > 1000)
    throw new Error('Notes exceed the allowed size.');
  const text = JSON.stringify(proof, Object.keys(proof).sort());
  if (new TextEncoder().encode(text).length > 12000)
    throw new Error('Manifest exceeds 12,000 bytes.');
  return text;
}
