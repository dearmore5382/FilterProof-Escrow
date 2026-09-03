// Uploads only the three synthetic images. Requires PINATA_JWT in the process
// environment and never writes the token to disk or output.
import { readFile, writeFile } from 'node:fs/promises';
import { File } from 'node:buffer';
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
if (!token) throw new Error('Provide PINATA_JWT through the environment or standard input; never paste it into source files.');
const endpoint = 'https://api.pinata.cloud/pinning/pinFileToIPFS';
const names = ['before.png', 'after.png', 'serial-gauge.png'];
const output = {};

for (const name of names) {
  const bytes = await readFile(new URL(name, import.meta.url));
  const body = new FormData();
  body.append('file', new File([bytes], name, { type: 'image/png' }));
  body.append('pinataMetadata', JSON.stringify({ name: `filterproof-synthetic-happy-v1-${name}` }));
  body.append('pinataOptions', JSON.stringify({ cidVersion: 1 }));
  const response = await fetch(endpoint, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body });
  const result = await response.json();
  if (!response.ok || typeof result.IpfsHash !== 'string') throw new Error(`Pinata upload failed for ${name}: HTTP ${response.status}`);
  output[name] = {
    cid: result.IpfsHash,
    pin_size_bytes: result.PinSize,
    timestamp: result.Timestamp,
    duplicate: Boolean(result.isDuplicate),
    gateway_url: `https://gateway.pinata.cloud/ipfs/${result.IpfsHash}`,
  };
  await writeFile(
    new URL('pinata-images.json', import.meta.url),
    JSON.stringify({ uploaded_at: new Date().toISOString(), complete: false, files: output }, null, 2) + '\n',
  );
}

await writeFile(
  new URL('pinata-images.json', import.meta.url),
  JSON.stringify({ uploaded_at: new Date().toISOString(), complete: true, files: output }, null, 2) + '\n',
);
console.log('Uploaded three synthetic fixtures. CIDs saved to pinata-images.json; PINATA_JWT was not stored.');
