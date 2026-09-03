// Uploads the exact generated manifest. The JWT is read from one stdin line
// (or PINATA_JWT) and is never written to disk or output.
import { readFile, writeFile } from 'node:fs/promises';
import { File } from 'node:buffer';
import { createHash } from 'node:crypto';
import { createInterface } from 'node:readline/promises';

async function tokenFromStdin() {
  const input = createInterface({ input: process.stdin, output: process.stdout, terminal: false });
  try {
    return (await input.question('')).trim();
  } finally {
    input.close();
  }
}

const token = process.env.PINATA_JWT || await tokenFromStdin();
if (!token) throw new Error('Provide PINATA_JWT through the environment or standard input.');
const bytes = await readFile(new URL('manifest.json', import.meta.url));
const sha256 = createHash('sha256').update(bytes).digest('hex');
const body = new FormData();
body.append('file', new File([bytes], 'manifest.json', { type: 'application/json' }));
body.append('pinataMetadata', JSON.stringify({ name: 'filterproof-synthetic-happy-v1-manifest' }));
body.append('pinataOptions', JSON.stringify({ cidVersion: 1 }));
const response = await fetch('https://api.pinata.cloud/pinning/pinFileToIPFS', {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
  body,
});
const result = await response.json();
if (!response.ok || typeof result.IpfsHash !== 'string') {
  throw new Error(`Pinata manifest upload failed: HTTP ${response.status}`);
}
const output = {
  uploaded_at: new Date().toISOString(),
  cid: result.IpfsHash,
  pin_size_bytes: result.PinSize,
  content_bytes: bytes.length,
  sha256,
  duplicate: Boolean(result.isDuplicate),
  gateway_url: `https://gateway.pinata.cloud/ipfs/${result.IpfsHash}`,
  gateway_verified: false,
};
await writeFile(new URL('pinata-manifest.json', import.meta.url), JSON.stringify(output, null, 2) + '\n');
console.log('Uploaded exact manifest. Public metadata saved; PINATA_JWT was not stored.');
