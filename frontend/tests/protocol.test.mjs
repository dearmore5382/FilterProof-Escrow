import test from 'node:test';
import assert from 'node:assert/strict';
import {
  uint,
  genAmount,
  recoveryTimestamp,
  addressOK,
  assertReceipt,
  verifyReadback,
  verifyNativeTransfer,
  verifiedStage,
  loadJournal,
} from '../lib/protocol.mjs';
const address = '0x' + '1'.repeat(40),
  contract = '0x' + '2'.repeat(40),
  hash = '0x' + 'a'.repeat(64);
const record = {
  chainId: 61999,
  hash,
  sender: address,
  contract,
  method: 'fund_job',
  args: ['0'],
  value: '1000',
};
const tx = {
  hash,
  from_address: address,
  to_address: contract,
  statusName: 'FINALIZED',
  value: 1000,
  resultName: 'MAJORITY_AGREE',
  consensus_data: {
    leader_receipt: [
      { execution_result: 'SUCCESS', result: { status: 'return' } },
    ],
  },
};
const call = { method: 'fund_job', args: [0n] };
test('amount precision and unsigned bounds', () => {
  assert.equal(genAmount('1.000000000000000001'), 1000000000000000001n);
  for (const x of ['-1', '1e18', '1.1234567890123456789', '0', '01'])
    assert.throws(() => genAmount(x));
  assert.throws(() => uint(2n ** 256n));
  assert.equal(addressOK('0x' + '0'.repeat(40)), false);
});
test('recovery time is canonical UTC accepted by the contract', () => {
  assert.match(
    recoveryTimestamp('2030-01-01T07:00'),
    /^2030-01-01T00:00:00Z$/,
  );
  assert.throws(() => recoveryTimestamp('not-a-date'));
});
test('FINALIZED alone never passes', () => {
  assert.equal(
    assertReceipt(tx, record, 61999, call, 'FUNDED').stage,
    'READBACK_REQUIRED',
  );
  assert.throws(() =>
    assertReceipt(
      { ...tx, consensus_data: undefined },
      record,
      61999,
      call,
      'FUNDED',
    ),
  );
  assert.throws(() =>
    assertReceipt(
      { ...tx, resultName: 'MAJORITY_DISAGREE' },
      record,
      61999,
      call,
      'FUNDED',
    ),
  );
});
test('receipt identity and contract rejection', () => {
  for (const bad of [
    { hash: '0x' + 'b'.repeat(64) },
    { from_address: contract },
    { to_address: address },
    { value: 999 },
  ])
    assert.throws(() =>
      assertReceipt({ ...tx, ...bad }, record, 61999, call, 'FUNDED'),
    );
  assert.throws(() => assertReceipt(tx, record, 61999, call, 'OPERATOR_ONLY'));
  assert.throws(() =>
    assertReceipt(tx, record, 61999, { ...call, args: [1n] }, 'FUNDED'),
  );
});
test('pending is not failed or resubmitted', () => {
  assert.equal(
    assertReceipt(
      { ...tx, statusName: 'COMMITTING' },
      record,
      61999,
      call,
      undefined,
    ).stage,
    'PENDING',
  );
});
test('readback mismatch blocks completion', () => {
  assert.throws(() => verifyReadback(record, 'FUNDED', { status: 'DRAFT' }));
  assert.equal(
    verifyReadback(record, 'FUNDED', {
      status: 'FUNDED',
      bounty: '1000',
      held: '1000',
      paid: '0',
      refunded: '0',
    }),
    true,
  );
});
test('corrupt journals fail closed', () => {
  assert.deepEqual(loadJournal(null), []);
  assert.deepEqual(loadJournal(JSON.stringify([record])), [record]);
  for (const raw of ['oops', '{}', '[{}]'])
    assert.throws(() => loadJournal(raw));
});
test('fractional GEN does not round or reject leading fractional zeros', () => {
  assert.equal(genAmount('0.1'), 100000000000000000n);
  assert.equal(genAmount('0.000000000000000001'), 1n);
});
test('settlement stays pending until its exact native transfer finalizes', () => {
  const settlement = {
    ...record,
    method: 'execute_release',
    value: '0',
  };
  const job = {
    operator: '0x' + '3'.repeat(40),
    technician: '0x' + '4'.repeat(40),
    bounty: '1000',
  };
  assert.equal(
    verifyNativeTransfer({ triggered_transactions: [] }, [], settlement, job)
      .stage,
    'TRANSFER_PENDING',
  );
  const childHash = '0x' + 'b'.repeat(64);
  const child = {
    hash: childHash,
    status: 'FINALIZED',
    type: 0,
    from_address: contract,
    to_address: job.technician,
    triggered_by: hash,
    value: 1000,
    value_credited: true,
  };
  const result = verifyNativeTransfer(
    { triggered_transactions: [childHash] },
    [child],
    settlement,
    job,
  );
  assert.deepEqual(result, { stage: 'TRANSFER_VERIFIED', childHash });
  assert.equal(verifiedStage(result.stage), true);
  assert.equal(
    verifyNativeTransfer(
      { triggered_transactions: [childHash] },
      [{ ...child, type: undefined }],
      settlement,
      job,
    ).stage,
    'TRANSFER_VERIFIED',
  );
  assert.throws(() =>
    verifyNativeTransfer(
      { triggered_transactions: [childHash] },
      [{ ...child, to_address: job.operator }],
      settlement,
      job,
    ),
  );
});
