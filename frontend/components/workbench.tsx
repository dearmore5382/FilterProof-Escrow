'use client';
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type SyntheticEvent,
} from 'react';
import { createClient, abi } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionHashVariant } from 'genlayer-js/types';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import deployment from '@/lib/deployment.json';
import {
  addressOK,
  same,
  hashOK,
  uint,
  genAmount,
  parseJob,
  assertReceipt,
  verifyReadback,
  verifyNativeTransfer,
  settlementMethod,
  verifiedStage,
  loadJournal,
} from '@/lib/protocol.mjs';

type Provider = NonNullable<Parameters<typeof createClient>[0]>['provider'];
type Entry = {
  hash: string;
  chainId: number;
  sender: string;
  contract: string;
  method: string;
  args: string[];
  value: string;
  stage: string;
  detail: string;
  childHash?: string;
  createdAt: string;
};
type Job = ReturnType<typeof parseJob>;
const address = deployment.contractAddress as `0x${string}`;
const explorer = 'https://explorer-studio.genlayer.com';
const configured =
  addressOK(address) &&
  /^[a-f0-9]{64}$/.test(deployment.sourceSha256) &&
  deployment.liveAuditVerified;
const client = createClient({ chain: studionet });
const journalKey = 'filterproof:journal:v1';
const intentKey = 'filterproof:submission-intent:v1';
const asHex = (value: string) => value as `0x${string}`;
const formText = (form: FormData, key: string) => {
  const value = form.get(key);
  if (typeof value !== 'string') throw new Error('Missing text field: ' + key);
  return value.trim();
};
const messageOf = (e: unknown) =>
  e instanceof Error ? e.message : 'The operation could not be completed.';
const encoded = (value: unknown) => {
  if (
    !value ||
    typeof value !== 'object' ||
    !('raw' in value) ||
    !Array.isArray(value.raw)
  )
    throw new Error('Receipt calldata is unavailable.');
  return abi.calldata.decode(new Uint8Array(value.raw));
};

export function Workbench() {
  const [wallet, setWallet] = useState(''),
    [notice, setNotice] = useState(''),
    [busy, setBusy] = useState(false),
    [ready, setReady] = useState(false);
  const [rows, setRows] = useState<Entry[]>([]),
    [journalError, setJournalError] = useState(''),
    [job, setJob] = useState<Job | null>(null),
    [jobId, setJobId] = useState('0'),
    [recoveryHash, setRecoveryHash] = useState('');
  const rowsRef = useRef<Entry[]>([]);
  const lock = useRef(false);
  const alive = useRef(true);
  const save = useCallback((next: Entry[]) => {
    localStorage.setItem(journalKey, JSON.stringify(next));
    rowsRef.current = next;
    setRows(next);
  }, []);
  const readJob = useCallback(async (id: string) => {
    const args = [uint(id)];
    const [raw, money] = await Promise.all(
      ['get_job', 'get_accounting'].map((functionName) =>
        client.readContract({
          address,
          functionName,
          args,
          transactionHashVariant: TransactionHashVariant.LATEST_FINAL,
        }),
      ),
    );
    return parseJob(raw, money);
  }, []);
  async function parity() {
    if (!configured)
      throw new Error('Contract is not configured and live-audit verified.');
    const chainId = await client.getChainId();
    if (chainId !== studionet.id) throw new Error('RPC chain mismatch.');
    const code = await client.getContractCode(address);
    const bytes = code.startsWith('0x')
      ? new Uint8Array(
          code
            .slice(2)
            .match(/.{2}/g)!
            .map((x) => parseInt(x, 16)),
        )
      : new TextEncoder().encode(code);
    const digest = Array.from(
      new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
      (b) => b.toString(16).padStart(2, '0'),
    ).join('');
    if (digest !== deployment.sourceSha256)
      throw new Error(
        'Deployed source does not match the approved source hash.',
      );
  }
  const reconcile = useCallback(
    async (record: Entry) => {
      if (
        !configured ||
        record.contract.toLowerCase() !== address.toLowerCase() ||
        record.chainId !== studionet.id
      )
        return;
      try {
        const [tx, chainId] = await Promise.all([
          client.getTransaction({
            hash: record.hash as Parameters<
              typeof client.getTransaction
            >[0]['hash'],
          }),
          client.getChainId(),
        ]);
        if ((tx.statusName ?? tx.status) !== 'FINALIZED') {
          const stage = String(tx.statusName ?? tx.status);
          save(
            rowsRef.current.map((r) =>
              r.hash === record.hash ? { ...r, detail: stage } : r,
            ),
          );
          return;
        }
        // SDK decodes calldata/result into raw bytes plus human-readable text.
        // Decode the raw bytes, never infer a new ID from global counters.
        const receipts = tx.consensus_data?.leader_receipt;
        const leader = Array.isArray(receipts) ? receipts.at(-1) : receipts;
        const data = tx.data?.calldata ?? leader?.calldata;
        const decoded = encoded(data);
        if (!(decoded instanceof Map))
          throw new Error('Receipt call is malformed.');
        const result = leader?.result as unknown as {
          status: string;
          payload: unknown;
        };
        const returned = encoded(result?.payload);
        if (
          typeof returned !== 'string' &&
          typeof returned !== 'bigint' &&
          typeof returned !== 'number'
        )
          throw new Error('Unexpected transaction return type.');
        const call = {
          method: decoded.get('method'),
          args: decoded.get('args'),
        };
        const checked = assertReceipt(tx, record, chainId, call, returned);
        if (checked.stage !== 'READBACK_REQUIRED') return;
        const id =
          record.method === 'create_job' ? String(returned) : record.args[0];
        const current = await readJob(id);
        const attempt =
          record.method === 'submit_proof'
            ? await client.readContract({
                address,
                functionName: 'get_attempt',
                args: [uint(returned)],
                transactionHashVariant: TransactionHashVariant.LATEST_FINAL,
              })
            : undefined;
        verifyReadback(record, String(returned), current, attempt);
        const childHashes = settlementMethod(record.method)
          ? ((tx as unknown as { triggered_transactions?: string[] })
              .triggered_transactions ?? [])
          : [];
        const children = await Promise.all(
          childHashes.map((hash) =>
            client.getTransaction({
              hash: hash as Parameters<
                typeof client.getTransaction
              >[0]['hash'],
            }),
          ),
        );
        const transfer = verifyNativeTransfer(
          tx,
          children,
          record,
          current,
        );
        save(
          rowsRef.current.map((r) =>
            r.hash === record.hash
              ? {
                  ...r,
                  stage: transfer.stage,
                  childHash: transfer.childHash,
                  detail:
                    transfer.stage === 'TRANSFER_PENDING'
                      ? `${String(returned)} · Job ${id} · awaiting native transfer finality`
                      : transfer.stage === 'TRANSFER_VERIFIED'
                        ? `${String(returned)} · Job ${id} · native transfer ${transfer.childHash}`
                        : `${String(returned)} · Job ${id}`,
                }
              : r,
          ),
        );
        if (alive.current) {
          setJobId(id);
          setJob(current);
        }
      } catch (e) {
        save(
          rowsRef.current.map((r) =>
            r.hash === record.hash
              ? { ...r, stage: 'NEEDS_REVIEW', detail: messageOf(e) }
              : r,
          ),
        );
      }
    },
    [readJob, save],
  );
  useEffect(() => {
    alive.current = true;
    // Synchronize browser-only storage after hydration, not during SSR.
    queueMicrotask(() => {
      if (!alive.current) return;
      try {
        const initial = loadJournal(localStorage.getItem(journalKey));
        rowsRef.current = initial;
        setRows(initial);
        if (localStorage.getItem(intentKey))
          setJournalError(
            'An interrupted submission needs reconciliation. Recover its hash from your wallet; do not submit again.',
          );
      } catch (e) {
        setJournalError(messageOf(e));
      }
    });
    let polling = false;
    const timer = setInterval(async () => {
      if (polling) return;
      polling = true;
      try {
        for (const r of rowsRef.current.filter((r) =>
          ['PENDING', 'TRANSFER_PENDING'].includes(r.stage),
        ))
          await reconcile(r);
      } finally {
        polling = false;
      }
    }, 8000);
    const provider = (window as unknown as { ethereum?: Provider }).ethereum;
    const changed = () => {
      setWallet('');
      setReady(false);
      setNotice('Wallet or network changed. Reconnect before writing.');
    };
    provider?.on?.('accountsChanged', changed);
    provider?.on?.('chainChanged', changed);
    const storage = (event: StorageEvent) => {
      if (event.key === journalKey) {
        try {
          const next = loadJournal(event.newValue);
          rowsRef.current = next;
          setRows(next);
        } catch (e) {
          setJournalError(messageOf(e));
        }
      }
    };
    window.addEventListener('storage', storage);
    return () => {
      alive.current = false;
      clearInterval(timer);
      provider?.removeListener?.('accountsChanged', changed);
      provider?.removeListener?.('chainChanged', changed);
      window.removeEventListener('storage', storage);
    };
  }, [reconcile]);
  async function connect() {
    setBusy(true);
    try {
      const provider = (window as unknown as { ethereum?: Provider }).ethereum;
      if (!provider)
        throw new Error('Install an EIP-1193 browser wallet to connect.');
      const accounts = (await provider.request({
        method: 'eth_requestAccounts',
      })) as string[];
      if (!addressOK(accounts[0]))
        throw new Error('No valid wallet account selected.');
      await provider.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: '0x' + studionet.id.toString(16) }],
      });
      await parity();
      setWallet(accounts[0]);
      setReady(true);
      setNotice('Wallet connected. Contract source verified.');
    } catch (e) {
      setNotice(messageOf(e));
      setReady(false);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    const requested = () => void connect();
    window.addEventListener('filterproof:connect-wallet', requested);
    return () =>
      window.removeEventListener('filterproof:connect-wallet', requested);
  }, []);
  async function verifyPublishedRun() {
    setBusy(true);
    setNotice('Reading the published StudioNet lifecycle…');
    try {
      await parity();
      const id = deployment.verifiedRun.jobId;
      const current = await readJob(id);
      if (
        current.status !== 'PAID' ||
        current.held !== '0' ||
        current.paid !== current.bounty ||
        current.refunded !== '0'
      )
        throw new Error('Published job accounting no longer matches PAID readback.');
      const [parent, child] = await Promise.all([
        client.getTransaction({
          hash: deployment.verifiedRun.settleTx as Parameters<
            typeof client.getTransaction
          >[0]['hash'],
        }),
        client.getTransaction({
          hash: deployment.verifiedRun.transferTx as Parameters<
            typeof client.getTransaction
          >[0]['hash'],
        }),
      ]);
      if (
        !same(parent.hash ?? parent.txId, deployment.verifiedRun.settleTx) ||
        !same(parent.to_address ?? parent.recipient, address) ||
        (parent.statusName ?? parent.status) !== 'FINALIZED'
      )
        throw new Error('Published settlement transaction is not finalized.');
      const transfer = verifyNativeTransfer(
        parent,
        [child],
        {
          hash: deployment.verifiedRun.settleTx,
          chainId: studionet.id,
          sender: current.operator,
          contract: address,
          method: 'execute_release',
          args: [id],
          value: '0',
          stage: 'PENDING',
          detail: '',
          createdAt: '',
        },
        current,
      );
      if (transfer.stage !== 'TRANSFER_VERIFIED')
        throw new Error('Published native payout is not finalized yet.');
      setJobId(id);
      setJob(current);
      setNotice(
        `Verified live job ${id}: PAID readback and exact native transfer ${transfer.childHash}.`,
      );
    } catch (e) {
      setNotice(messageOf(e));
    } finally {
      setBusy(false);
    }
  }
  async function send(method: string, args: (string | bigint)[], value = 0n) {
    if (!navigator.locks) {
      setNotice(
        'This browser cannot coordinate safe submissions across tabs. Use a browser with Web Locks support.',
      );
      return;
    }
    await navigator.locks.request(
      'filterproof:submit',
      { ifAvailable: true },
      async (acquired) => {
        if (!acquired) {
          setNotice(
            'Another tab is submitting. Wait and reconcile its transaction.',
          );
          return;
        }
        await sendLocked(method, args, value);
      },
    );
  }
  async function sendLocked(
    method: string,
    args: (string | bigint)[],
    value = 0n,
  ) {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    try {
      if (!ready || !wallet || journalError)
        throw new Error(
          'Connect a verified wallet and resolve journal errors first.',
        );
      if (localStorage.getItem(intentKey))
        throw new Error(
          'A prior submission is unresolved. Recover its transaction hash first.',
        );
      rowsRef.current = loadJournal(localStorage.getItem(journalKey));
      if (rowsRef.current.some((r) => !verifiedStage(r.stage)))
        throw new Error(
          'Reconcile the existing transaction before submitting another.',
        );
      if (rowsRef.current.length >= 500)
        throw new Error(
          'Journal limit reached. Export the journal before starting a new browser profile.',
        );
      const provider = (window as unknown as { ethereum?: Provider }).ethereum;
      if (!provider) throw new Error('Wallet disconnected.');
      const accounts = (await provider.request({
        method: 'eth_accounts',
      })) as string[];
      const chain = await provider.request({ method: 'eth_chainId' });
      if (
        accounts[0]?.toLowerCase() !== wallet.toLowerCase() ||
        Number(chain) !== studionet.id
      )
        throw new Error('Wallet identity changed. Reconnect.');
      await parity();
      // Check journal persistence before asking the wallet to submit.
      save(rowsRef.current);
      const writer = createClient({
        chain: studionet,
        account: asHex(wallet),
        provider,
      });
      const intent = {
        chainId: studionet.id,
        contract: address,
        sender: wallet,
        method,
        args: args.map(String),
        value: String(value),
        createdAt: new Date().toISOString(),
      };
      localStorage.setItem(intentKey, JSON.stringify(intent));
      setNotice('Confirm the transaction in your wallet.');
      let hash: unknown;
      try {
        hash = await writer.writeContract({
          address,
          functionName: method,
          args,
          value,
          leaderOnly: false,
        });
      } catch (e) {
        // Only an explicit user rejection proves that signing did not occur.
        if (
          typeof e === 'object' &&
          e !== null &&
          'code' in e &&
          e.code === 4001
        )
          localStorage.removeItem(intentKey);
        else
          setJournalError(
            'Submission outcome is unknown. Check your wallet and recover the hash before sending again.',
          );
        throw e;
      }
      if (typeof hash !== 'string' || !hashOK(hash))
        throw new Error(
          'Wallet returned an invalid hash. Keep the submission intent for manual reconciliation.',
        );
      const record: Entry = {
        hash: String(hash),
        chainId: studionet.id,
        contract: address,
        sender: wallet,
        method,
        args: args.map(String),
        value: String(value),
        stage: 'PENDING',
        detail: 'Submitted; awaiting finality.',
        createdAt: new Date().toISOString(),
      };
      try {
        save([...rowsRef.current, record]);
        localStorage.removeItem(intentKey);
      } catch {
        rowsRef.current = [...rowsRef.current, record];
        setRows(rowsRef.current);
        setJournalError(
          `Storage failed after submission. Save this hash: ${String(hash)}. Do not submit again.`,
        );
      }
      setNotice(
        `Submitted ${String(hash)}. The same hash will be reconciled; no automatic resubmission.`,
      );
    } catch (e) {
      setNotice(messageOf(e));
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  async function recoverIntent() {
    try {
      if (!hashOK(recoveryHash))
        throw new Error(
          'Enter the complete transaction hash from your wallet.',
        );
      const raw = localStorage.getItem(intentKey);
      if (!raw) throw new Error('No interrupted submission intent exists.');
      const intent = JSON.parse(raw);
      const entry = {
        ...intent,
        hash: recoveryHash,
        stage: 'PENDING',
        detail: 'Recovered hash; not yet verified.',
      };
      const validated = loadJournal(JSON.stringify([entry]));
      save([
        ...rowsRef.current.filter((r) => r.hash !== recoveryHash),
        ...validated,
      ]);
      localStorage.removeItem(intentKey);
      setJournalError('');
      await reconcile(entry);
    } catch (e) {
      setNotice(messageOf(e));
    }
  }
  async function create(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const form = new FormData(event.currentTarget);
      const get = (key: string) => formText(form, key);
      const deadline = new Date(get('deadline'))
        .toISOString()
        .replace('.000Z', '');
      if (!addressOK(get('technician')))
        throw new Error('Invalid technician address.');
      await send('create_job', [
        get('title'),
        get('site'),
        get('serial'),
        get('filters'),
        get('technician'),
        genAmount(get('bounty')),
        deadline,
      ]);
    } catch (e) {
      setNotice(messageOf(e));
    }
  }
  async function submit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const f = new FormData(event.currentTarget);
    try {
      await send('submit_proof', [
        uint(jobId),
        formText(f, 'url'),
        formText(f, 'hash'),
      ]);
    } catch (e) {
      setNotice(messageOf(e));
    }
  }
  function exportJournal() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(rows, null, 2)], { type: 'application/json' }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = 'filterproof-transaction-journal.json';
    a.click();
    URL.revokeObjectURL(url);
  }
  const disabled =
    !ready ||
    busy ||
    !!journalError ||
    rows.some((r) => !verifiedStage(r.stage));
  return (
    <section className="panel">
      <div className="panel-title">
        <div>
          <p className="eyebrow">ON-CHAIN WORKSPACE</p>
          <h2>Work orders & settlement</h2>
        </div>
        <span className="wallet-state">
          {wallet ? `Connected · ${wallet.slice(0, 6)}…${wallet.slice(-4)}` : 'Wallet not connected'}
        </span>
      </div>
      <p className="muted">
        Studionet · Chain {studionet.id} ·{' '}
        {configured ? address : 'Contract not configured'}
      </p>
      <output className="feedback">{notice}</output>
      <section className="live-verification" aria-label="Verified live lifecycle">
        <div>
          <p className="eyebrow">PUBLISHED STUDIO NETWORK PROOF</p>
          <h3>Complete funded lifecycle · Job {deployment.verifiedRun.jobId}</h3>
          <p className="muted">
            Create, exact funding, proof, assessment and payout are public. The
            verification button rereads PAID accounting and the finalized child
            transfer from StudioNet.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={verifyPublishedRun}
          disabled={!configured || busy}
        >
          Verify live payout
        </Button>
        <div className="live-links">
          {[
            ['Create', deployment.verifiedRun.createTx],
            ['Fund', deployment.verifiedRun.fundTx],
            ['Proof', deployment.verifiedRun.proofTx],
            ['Assess', deployment.verifiedRun.assessTx],
            ['Payout', deployment.verifiedRun.settleTx],
            ['Native transfer', deployment.verifiedRun.transferTx],
          ].map(([label, hash]) => (
            <a
              key={label}
              href={`${explorer}/transactions/${hash}`}
              target="_blank"
              rel="noreferrer"
            >
              {label}
            </a>
          ))}
        </div>
      </section>
      {journalError && (
        <div>
          <p role="alert">{journalError}</p>
          <label>
            Recover interrupted transaction hash
            <input
              value={recoveryHash}
              onChange={(e) => setRecoveryHash(e.target.value.trim())}
            />
          </label>
          <Button
            variant="outline"
            onClick={recoverIntent}
            disabled={!configured}
          >
            Recover existing hash
          </Button>
        </div>
      )}
      <Tabs defaultValue="manage">
        <TabsList>
          <TabsTrigger value="manage">Manage order</TabsTrigger>
          <TabsTrigger value="create">Create order</TabsTrigger>
          <TabsTrigger value="journal">
            Transaction journal ({rows.length})
          </TabsTrigger>
        </TabsList>
        <TabsContent value="manage">
          <div className="load-row">
            <label>
              Job ID
              <input
                value={jobId}
                onChange={(e) => {
                  setJobId(e.target.value);
                  setJob(null);
                }}
                inputMode="numeric"
              />
            </label>
            <Button
              disabled={!configured || busy}
              onClick={async () => {
                try {
                  await parity();
                  setJob(await readJob(jobId));
                } catch (e) {
                  setNotice(messageOf(e));
                }
              }}
            >
              Load finalized state
            </Button>
          </div>
          {job ? (
            <>
              <h3>{job.title}</h3>
              <dl className="job-details">
                {Object.entries(job).map(([k, v]) => (
                  <div key={k}>
                    <dt>{k}</dt>
                    <dd>{v}</dd>
                  </div>
                ))}
              </dl>
              <p className="muted">
                Amounts above are in attoGEN (10¹⁸ attoGEN = 1 GEN). Settlement
                is shown as complete only after authoritative accounting
                readback and the exact emitted native transfer both finalize.
              </p>
              <div className="actions">
                {[
                  ['fund_job', 'Fund exact bounty', 'DRAFT'],
                  ['cancel_draft', 'Cancel draft', 'DRAFT'],
                  ['assess_proof', 'Assess evidence', 'PROOF_READY'],
                  ['execute_release', 'Execute payout', 'RELEASE_AUTHORIZED'],
                  ['execute_refund', 'Execute refund', 'REFUND_AUTHORIZED'],
                  [
                    'recover_expired',
                    'Recover expired funds',
                    'FUNDED,CORRECTION_REQUIRED,PROOF_READY',
                  ],
                ].map(([method, label, status]) => (
                  <Button
                    key={method}
                    variant="outline"
                    disabled={
                      disabled ||
                      !status.split(',').includes(job.status) ||
                      (['fund_job', 'cancel_draft'].includes(method) &&
                        wallet.toLowerCase() !== job.operator.toLowerCase())
                    }
                    onClick={() =>
                      send(
                        method,
                        [uint(jobId)],
                        method === 'fund_job' ? uint(job.bounty) : 0n,
                      )
                    }
                  >
                    {label}
                  </Button>
                ))}
              </div>
              <form onSubmit={submit}>
                <h3>Submit hash-bound proof</h3>
                <label>
                  Manifest HTTPS URL
                  <input name="url" type="url" required maxLength={500} />
                </label>
                <label>
                  Manifest SHA-256
                  <input
                    name="hash"
                    required
                    pattern="[a-f0-9]{64}"
                    maxLength={64}
                  />
                </label>
                <Button
                  type="submit"
                  disabled={
                    disabled ||
                    wallet.toLowerCase() !== job.technician.toLowerCase() ||
                    !['FUNDED', 'CORRECTION_REQUIRED'].includes(job.status)
                  }
                >
                  Submit proof
                </Button>
              </form>
            </>
          ) : (
            <p className="muted">
              Load an order to inspect sealed inputs, custody and available
              actions. No sample balances are shown.
            </p>
          )}
        </TabsContent>
        <TabsContent value="create">
          <form onSubmit={create}>
            <div className="field-grid">
              {[
                ['title', 'Work order title', 120],
                ['site', 'Site code', 80],
                ['serial', 'Asset serial number', 100],
                ['filters', 'Required filter set', 500],
                ['technician', 'Technician wallet', 42],
                ['bounty', 'Bounty (GEN)', 80],
              ].map(([key, label, max]) => (
                <label key={key}>
                  {label}
                  <input
                    name={String(key)}
                    maxLength={Number(max)}
                    required
                    pattern={
                      key === 'bounty' ? '[0-9]+(\\.[0-9]{1,18})?' : '[^|]+'
                    }
                  />
                </label>
              ))}
              <label>
                Recovery deadline (local time)
                <input name="deadline" type="datetime-local" required />
              </label>
            </div>
            <p className="muted">
              Creation seals the scope but does not move funds. Funding is a
              separate, exact-value transaction.
            </p>
            <Button type="submit" disabled={disabled}>
              Create sealed work order
            </Button>
          </form>
        </TabsContent>
        <TabsContent value="journal">
          <Button variant="outline" onClick={exportJournal}>
            Export journal
          </Button>
          {!rows.length ? (
            <p className="muted">
              No transactions submitted from this browser.
            </p>
          ) : (
            rows.map((row) => (
              <article key={row.hash} className="journal-entry">
                <strong>
                  {row.method} · {row.stage}
                </strong>
                <a
                  href={`${explorer}/transactions/${row.hash}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  {row.hash}
                </a>
                <p>{row.detail}</p>
                {row.childHash && (
                  <a
                    href={`${explorer}/transactions/${row.childHash}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Native transfer: {row.childHash}
                  </a>
                )}
                <Button
                  variant="outline"
                  disabled={busy || !configured}
                  onClick={() => reconcile(row)}
                >
                  Recheck existing hash
                </Button>
              </article>
            ))
          )}
          <p className="muted">
            Finalized does not mean the requested action succeeded. Completion
            also requires successful execution, accepted consensus and matching
            readback. A timeout never submits another transaction.
          </p>
        </TabsContent>
      </Tabs>
    </section>
  );
}
