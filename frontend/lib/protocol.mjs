export const ZERO = '0x' + '0'.repeat(40);
export const addressOK = (value) =>
  typeof value === 'string' &&
  /^0x[0-9a-fA-F]{40}$/.test(value) &&
  value.toLowerCase() !== ZERO;
export const hashOK = (value) =>
  typeof value === 'string' && /^0x[0-9a-fA-F]{64}$/.test(value);
export const same = (a, b) =>
  typeof a === 'string' &&
  typeof b === 'string' &&
  a.toLowerCase() === b.toLowerCase();
export function uint(value) {
  const s = String(value);
  if (!/^(0|[1-9]\d*)$/.test(s) || BigInt(s) >= 2n ** 256n)
    throw new Error('Enter an unsigned 256-bit integer.');
  return BigInt(s);
}
export function genAmount(value) {
  if (!/^(0|[1-9]\d*)(\.\d{1,18})?$/.test(String(value)))
    throw new Error('GEN amount must be positive with at most 18 decimals.');
  const [whole, fraction = ''] = String(value).split('.');
  const amount = uint(
    BigInt(whole) * 10n ** 18n + BigInt(fraction.padEnd(18, '0')),
  );
  if (!amount) throw new Error('GEN amount must be positive.');
  return amount;
}
export function parseJob(raw, money) {
  if (
    typeof raw !== 'string' ||
    typeof money !== 'string' ||
    raw === 'NOT_FOUND' ||
    money === 'NOT_FOUND'
  )
    throw new Error('Work order not found.');
  const p = raw.split('|'),
    a = money.split('|');
  if (p.length !== 9 || a.length !== 5 || !addressOK(p[1]) || !addressOK(p[2]))
    throw new Error('Malformed contract readback.');
  a.forEach(uint);
  uint(p[8]);
  return {
    status: p[0],
    operator: p[1],
    technician: p[2],
    title: p[3],
    site: p[4],
    serial: p[5],
    filters: p[6],
    deadline: p[7],
    attempts: p[8],
    bounty: a[0],
    held: a[1],
    paid: a[2],
    refunded: a[3],
    contractBalance: a[4],
  };
}
export function assertReceipt(tx, record, chainId, call, returned) {
  if (chainId !== record.chainId) throw new Error('RPC chain mismatch.');
  if (
    !same(tx.hash ?? tx.txId, record.hash) ||
    !same(tx.from_address ?? tx.sender, record.sender) ||
    !same(tx.to_address ?? tx.recipient, record.contract)
  )
    throw new Error('Receipt identity mismatch.');
  if ((tx.statusName ?? tx.status) !== 'FINALIZED') return { stage: 'PENDING' };
  const receipts = tx.consensus_data?.leader_receipt;
  const leader = Array.isArray(receipts) ? receipts.at(-1) : receipts;
  if (
    !leader ||
    leader.execution_result !== 'SUCCESS' ||
    leader.result?.status !== 'return'
  )
    throw new Error('Finalized transaction did not execute successfully.');
  const votes = Object.values(tx.consensus_data?.votes ?? {});
  const majority =
    votes.length >= 3 &&
    votes.filter((v) => v === 'agree').length > votes.length / 2;
  if (tx.resultName ? tx.resultName !== 'MAJORITY_AGREE' : !majority)
    throw new Error('Consensus agreement is missing or rejected.');
  if (
    !call ||
    call.method !== record.method ||
    JSON.stringify(call.args.map(String)) !==
      JSON.stringify(record.args.map(String))
  )
    throw new Error('Receipt method or arguments mismatch.');
  if (String(tx.value) !== record.value)
    throw new Error('Receipt value mismatch.');
  const allowed = {
    fund_job: ['FUNDED'],
    cancel_draft: ['CANCELLED'],
    assess_proof: [
      'RELEASE_AUTHORIZED',
      'CORRECTION_REQUIRED',
      'REFUND_AUTHORIZED',
    ],
    execute_release: ['PAID'],
    execute_refund: ['REFUNDED'],
    recover_expired: ['EXPIRED_REFUNDED'],
  };
  if (record.method === 'create_job' || record.method === 'submit_proof')
    uint(returned);
  else if (!allowed[record.method]?.includes(returned))
    throw new Error('Contract rejected the operation: ' + String(returned));
  return { stage: 'READBACK_REQUIRED', returned: String(returned) };
}
export function verifyReadback(record, returned, job, attempt) {
  if (record.method === 'create_job') {
    const a = record.args;
    if (
      !same(job.operator, record.sender) ||
      !same(job.technician, a[4]) ||
      job.title !== a[0] ||
      job.site !== a[1] ||
      job.serial !== a[2] ||
      job.filters !== a[3] ||
      job.bounty !== a[5] ||
      job.deadline !== a[6]
    )
      throw new Error('Created order does not match sealed inputs.');
  } else if (record.method === 'submit_proof') {
    const p = String(attempt).split('|');
    if (
      p.length !== 8 ||
      p[1] !== record.args[0] ||
      p[5] !== record.args[2] ||
      p[7] !== record.args[1]
    )
      throw new Error('Submitted proof does not match readback.');
  } else if (job.status !== returned)
    throw new Error(
      'Current state differs from the transaction result; manual reconciliation is required.',
    );
  if (
    !['DRAFT', 'CANCELLED'].includes(job.status) &&
    uint(job.held) + uint(job.paid) + uint(job.refunded) !== uint(job.bounty)
  )
    throw new Error('Escrow accounting is not conserved.');
  if (
    record.method === 'fund_job' &&
    (job.held !== job.bounty || job.paid !== '0' || job.refunded !== '0')
  )
    throw new Error('Funding accounting mismatch.');
  if (
    record.method === 'execute_release' &&
    (job.held !== '0' || job.paid !== job.bounty)
  )
    throw new Error('Payout accounting mismatch.');
  if (
    ['execute_refund', 'recover_expired'].includes(record.method) &&
    (job.held !== '0' || job.refunded !== job.bounty)
  )
    throw new Error('Refund accounting mismatch.');
  return true;
}
export function loadJournal(text) {
  if (!text) return [];
  const rows = JSON.parse(text);
  if (
    !Array.isArray(rows) ||
    rows.length > 500 ||
    rows.some(
      (r) =>
        !hashOK(r.hash) ||
        !addressOK(r.sender) ||
        !addressOK(r.contract) ||
        !Array.isArray(r.args) ||
        typeof r.method !== 'string' ||
        typeof r.value !== 'string' ||
        !Number.isInteger(r.chainId),
    )
  )
    throw new Error(
      'Transaction journal is damaged. Export browser storage before repairing it.',
    );
  return rows;
}
