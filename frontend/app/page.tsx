'use client';
import { useEffect, useRef, useState, type SyntheticEvent } from 'react';
import Image from 'next/image';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import {
  ClipboardCheck,
  FileCheck2,
  LockKeyhole,
  ArrowRight,
  Download,
  ShieldCheck,
} from 'lucide-react';
import { Workbench } from '@/components/workbench';
import { canonicalHttps, validateManifest, validateImageBytes } from '@/lib/evidence.mjs';
import deployment from '@/lib/deployment.json';

const images = [
  ['before', '01', 'Before maintenance'],
  ['after', '02', 'After replacement'],
  ['serial_gauge', '03', 'Serial number & pressure gauge'],
];
async function sha(bytes: ArrayBuffer) {
  return Array.from(
    new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
    (b) => b.toString(16).padStart(2, '0'),
  ).join('');
}

export default function Home() {
  const [section, setSection] = useState('proof');
  const [connectNonce, setConnectNonce] = useState(0);
  const [headerWalletMessage, setHeaderWalletMessage] = useState('');
  const walletError = (error: unknown) => {
    const value = error as { code?: number; message?: string; shortMessage?: string };
    if (value?.code === 4001) return 'Connection rejected in the wallet. Please try again.';
    if (value?.code === -32002)
      return 'A wallet request is already open. Open the wallet extension and finish or reject it, then retry.';
    return value?.shortMessage || value?.message || `Wallet error${value?.code ? ` (${value.code})` : ''}.`;
  };
  const [manifest, setManifest] = useState('');
  const [digest, setDigest] = useState('');
  const prepared = useRef({ manifest: '', sha256: '' });
  useEffect(() => {
    prepared.current = { manifest, sha256: digest };
  }, [manifest, digest]);
  useEffect(() => {
    type Tool = {
      name: string;
      description: string;
      inputSchema: object;
      annotations: { readOnlyHint: boolean };
      execute: (input: unknown) => unknown;
    };
    const context = (
      document as Document & {
        modelContext?: {
          registerTool: (
            tool: Tool,
            options: { signal: AbortSignal },
          ) => void | Promise<void>;
        };
      }
    ).modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    const tool: Tool = {
      name: 'get_prepared_filterproof_manifest',
      description:
        'Read the exact manifest and SHA-256 already generated in the visible Proof Studio. Does not upload files or send transactions.',
      inputSchema: {
        type: 'object',
        properties: {},
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true },
      execute(input) {
        if (
          !input ||
          typeof input !== 'object' ||
          Array.isArray(input) ||
          Object.keys(input).length
        )
          throw new Error('Expected an empty object.');
        if (!prepared.current.manifest)
          throw new Error('No manifest has been prepared.');
        return prepared.current;
      },
    };
    try {
      void Promise.resolve(
        context.registerTool(tool, { signal: lifecycle.signal }),
      ).catch(() => {});
    } catch {
      /* Optional browser capability; visible workflow remains available. */
    }
    return () => lifecycle.abort();
  }, []);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  async function buildProof(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage('');
    setManifest('');
    setDigest('');
    try {
      const form = new FormData(event.currentTarget);
      const get = (key: string) => {
        const value = form.get(key);
        if (typeof value !== 'string')
          throw new Error('Missing text field: ' + key);
        return value.trim();
      };
      if (!/^(0|[1-9]\d*)$/.test(get('job_id')))
        throw new Error('Job ID must be a non-negative integer.');
      if (
        !/^0x[0-9a-fA-F]{40}$/.test(get('technician')) ||
        /^0x0{40}$/.test(get('technician'))
      )
        throw new Error('Enter a valid technician wallet address.');
      const proof: Record<string, string | number> = {
        schema: 'filterproof-service-v1',
        job_id: get('job_id'),
        site_code: get('site_code'),
        asset_serial: get('asset_serial'),
        technician: get('technician'),
        service_date: get('service_date'),
        installed_filters: get('installed_filters'),
        pressure_before_kpa: Number(get('pressure_before_kpa')),
        pressure_after_kpa: Number(get('pressure_after_kpa')),
        notes: get('notes'),
      };
      const hashes: string[] = [];
      const urls: string[] = [];
      for (const [key] of images) {
        const url = get(key + '_image_url');
        const file = form.get(key + '_file');
        if (!canonicalHttps(url))
          throw new Error(
            'Image URLs must use canonical HTTPS without query strings or fragments.',
          );
        if (!(file instanceof File) || !file.size || file.size > 4_000_000)
          throw new Error(
            'Each image must be non-empty and no larger than 4 MB.',
          );
        const bytes = await file.arrayBuffer();
        validateImageBytes(bytes);
        const hash = await sha(bytes);
        proof[key + '_image_url'] = url;
        proof[key + '_image_sha256'] = hash;
        hashes.push(hash);
        urls.push(url);
      }
      if (new Set(hashes).size !== 3 || new Set(urls).size !== 3)
        throw new Error(
          'All three images must have distinct URLs and file contents.',
        );
      const text = validateManifest(proof);
      const computedDigest = await sha(new TextEncoder().encode(text).buffer);
      setManifest(text);
      setDigest(computedDigest);
      setMessage(
        'Manifest created. Host this exact JSON file and the three original images. This tool does not upload files.',
      );
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : 'Unable to prepare evidence.',
      );
    } finally {
      setBusy(false);
    }
  }
  function download() {
    const url = URL.createObjectURL(
      new Blob([manifest], { type: 'application/json' }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = 'filterproof-manifest.json';
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <div className="workspace">
      <header className="topbar">
        <div className="brand">
          <Image
            src="/filterproof-logo.png"
            width={48}
            height={48}
            unoptimized
            alt="FilterProof — commercial water system maintenance"
          />
          <div>
            <strong>
              FilterProof <span>Escrow</span>
            </strong>
            <small>COMMERCIAL WATER SYSTEMS</small>
          </div>
        </div>
        <div className="header-actions">
          <span className="network">
            <i /> Studionet · Verified production
          </span>
          <Button
            className="header-wallet"
            onClick={async () => {
              const provider = (
                window as unknown as {
                  ethereum?: {
                    request: (request: { method: string }) => Promise<unknown>;
                  };
                }
              ).ethereum;
              if (!provider) {
                setHeaderWalletMessage('Install an EIP-1193 wallet first.');
                return;
              }
              try {
                const existing = (await provider.request({
                  method: 'eth_accounts',
                })) as string[];
                const accounts = existing.length
                  ? existing
                  : ((setHeaderWalletMessage('Choose an account in your wallet…'),
                    await provider.request({
                      method: 'eth_requestAccounts',
                    })) as string[]);
                if (!Array.isArray(accounts) || !accounts[0])
                  throw new Error('The wallet returned no account. Unlock it and try again.');
                setSection('orders');
                setConnectNonce((value) => value + 1);
                setHeaderWalletMessage('');
              } catch (error) {
                setHeaderWalletMessage(walletError(error));
              }
            }}
          >
            Connect wallet
          </Button>
          {headerWalletMessage && (
            <output className="header-wallet-message">
              {headerWalletMessage}
            </output>
          )}
        </div>
      </header>
      <main className="shell">
        <div className="page-heading">
          <div>
            <p className="eyebrow">EVIDENCE-BACKED MAINTENANCE</p>
            <h1>Filter replacement records</h1>
            <p className="muted">
              The right system. The right filters. Evidence you can review.
            </p>
          </div>
        </div>
        <div className="gate">
          <LockKeyhole size={20} />
          <div>
            <strong>Verified testnet contract — wallet writes enabled</strong>
            <p>
              {deployment.contractAddress} · Source {deployment.sourceSha256.slice(0, 12)}…
              {' '}Each state change requires an explicit wallet signature and authoritative contract readback.
            </p>
          </div>
        </div>
        <Tabs value={section} onValueChange={setSection}>
          <TabsList className="workflow-tabs">
            <TabsTrigger value="orders">
              <ClipboardCheck /> Work orders & transactions
            </TabsTrigger>
            <TabsTrigger value="proof">
              <FileCheck2 /> Prepare evidence
            </TabsTrigger>
          </TabsList>
          <TabsContent value="proof">
            <div className="content-grid">
              <section className="panel">
                <div className="panel-title">
                  <div>
                    <p className="eyebrow">PROOF STUDIO</p>
                    <h2>Build an evidence package</h2>
                  </div>
                  <span className="tag">SHA-256</span>
                </div>
                <p className="muted">
                  Details must match the sealed work order. Image files are
                  hashed locally on your device.
                </p>
                <form onSubmit={buildProof} inert={busy} onChange={() => { setManifest(''); setDigest(''); }}>
                  <div className="field-grid">
                    <label>
                      Job ID
                      <input
                        name="job_id"
                        placeholder="Example: 0"
                        required
                        inputMode="numeric"
                      />
                    </label>
                    <label>
                      Service date
                      <input name="service_date" type="date" required />
                    </label>
                    <label>
                      Site code
                      <input
                        name="site_code"
                        maxLength={80}
                        placeholder="HOTEL-BKK-07"
                        required
                      />
                    </label>
                    <label>
                      Asset serial number
                      <input
                        name="asset_serial"
                        maxLength={100}
                        placeholder="RO-SKID-991"
                        required
                      />
                    </label>
                    <label className="full">
                      Technician wallet
                      <input name="technician" placeholder="0x…" required />
                    </label>
                    <label className="full">
                      Installed filter set
                      <input
                        name="installed_filters"
                        maxLength={500}
                        placeholder="SED-5M, CARBON-10, RO-4040"
                        required
                      />
                    </label>
                    <label>
                      Pressure before (kPa)
                      <input
                        name="pressure_before_kpa"
                        type="number"
                        min="0"
                        max="5000"
                        step="1"
                        required
                      />
                    </label>
                    <label>
                      Pressure after (kPa)
                      <input
                        name="pressure_after_kpa"
                        type="number"
                        min="0"
                        max="5000"
                        step="1"
                        required
                      />
                    </label>
                  </div>
                  <div className="image-evidence">
                    {images.map(([key, n, title]) => (
                      <fieldset key={key}>
                        <legend>
                          <span>{n}</span>
                          {title}
                        </legend>
                        <label>
                          Original file for hashing
                          <input
                            name={key + '_file'}
                            type="file"
                            accept="image/png,image/jpeg"
                            required
                          />
                        </label>
                        <label>
                          HTTPS URL of this exact file
                          <input
                            name={key + '_image_url'}
                            type="url"
                            placeholder="https://…/image.png"
                            required
                          />
                        </label>
                      </fieldset>
                    ))}
                  </div>
                  <label>
                    Notes
                    <textarea
                      name="notes"
                      maxLength={1000}
                      rows={3}
                      placeholder="Briefly describe the service. Do not include sensitive personal information."
                    />
                  </label>
                  <Button size="lg" type="submit" disabled={busy}>
                    {busy ? 'Computing hashes…' : 'Validate & create manifest'}
                    <ArrowRight size={18} />
                  </Button>
                </form>
                <output className="feedback">{message}</output>
                {manifest && (
                  <div className="result">
                    <h3>Manifest ready to host</h3>
                    <label>
                      SHA-256
                      <textarea readOnly value={digest} rows={2} />
                    </label>
                    <Button variant="outline" onClick={download}>
                      <Download /> Download exact JSON
                    </Button>
                    <details>
                      <summary>View manifest contents</summary>
                      <pre>{manifest}</pre>
                    </details>
                  </div>
                )}
              </section>
              <aside>
                <section className="panel checklist">
                  <span className="round-icon">
                    <ShieldCheck />
                  </span>
                  <h2>Evidence, not just a claim</h2>
                  <ol>
                    <li>
                      <strong>Seal the scope</strong>
                      <p>
                        The system, filter set, technician and bounty are fixed
                        when the work order is created.
                      </p>
                    </li>
                    <li>
                      <strong>Cross-check three images</strong>
                      <p>
                        Before, after and serial/gauge views. Each file has its
                        own hash commitment.
                      </p>
                    </li>
                    <li>
                      <strong>Assess, then settle</strong>
                      <p>
                        Rules turn observations into an outcome. AI never
                        selects the payment recipient.
                      </p>
                    </li>
                  </ol>
                </section>
                <div className="disclaimer">
                  <strong>Important limitations</strong>
                  <p>
                    Images do not certify drinking-water safety, laboratory
                    results or actual capture time.
                  </p>
                  <p>
                    Keep customer names, private addresses and identity
                    documents out of public evidence.
                  </p>
                </div>
              </aside>
            </div>
          </TabsContent>
          <TabsContent value="orders">
            <Workbench connectNonce={connectNonce} />
          </TabsContent>
        </Tabs>
        <footer>
          FilterProof Escrow{' '}
          <span>
            Service evidence · Independent observations · Deterministic
            settlement
          </span>
        </footer>
      </main>
    </div>
  );
}
