'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {once} = require('node:events');
const {spawn} = require('node:child_process');
const {PersistentCreditLedger} = require('../runtime/persistent_credit_ledger.cjs');
const {decimalRateToNanos, loadOfflineProfile, createOfflineGateway} = require('../runtime/gemini_offline_gateway.cjs');
const {inspectRequestBudget} = require('../runtime/gemini_request_budget.cjs');
const SNAPSHOT = require('../runtime/gemini_price_snapshot.json');
const NOW = new Date('2026-10-24T09:00:00Z');
const MODEL = 'gemini-3.8-flash';
const URL = '/v1beta/models/' + MODEL + ':generateContent';
const BODY = JSON.stringify({contents: [{role: 'user', parts: [{text: 'DO_NOT_LOG_TEST_PRIVATE_PAYLOAD'}]}],
  generationConfig: {maxOutputTokens: 1, candidateCount: 1}});
function temp(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'twf-connected-'));
  t.after(() => fs.rmSync(directory, {force: true, recursive: true}));
  return path.join(directory, 'budget.sqlite');
}
async function start(options) {
  const gateway = createOfflineGateway({snapshot: SNAPSHOT, now: NOW, ...options});
  gateway.server.listen(0, '127.0.0.1'); await once(gateway.server, 'listening');
  gateway.origin = 'http://127.0.0.1:' + gateway.server.address().port;
  return gateway;
}
async function call(gateway, role = 'developer', body = BODY) {
  return fetch(gateway.origin + URL, {method: 'POST', headers: {'x-twf-role': role}, body});
}
function fixtureDependencies() {
  return {catalog: new Map([[MODEL, {approved: true, evidence: 'test-fixture://not-real-prices',
    inputNanosPerToken: 2500000000n, outputNanosPerToken: 2500000000n}]]),
  boundForRequest: async spec => ({kind: 'HOST_VERIFIED_UPPER_BOUND', requestSha256: spec.requestSha256,
    maxInputTokens: 1, maxChargedOutputTokens: 1}),
  transport: async () => ({modelVersion: MODEL,
    usageMetadata: {promptTokenCount: 1, candidatesTokenCount: 1, totalTokenCount: 2}})};
}
test('official decimal rates convert exactly without floating-point rounding', () => {
  assert.equal(decimalRateToNanos('0.75'), 75000n);
  assert.equal(decimalRateToNanos('3.75'), 375000n);
  for (const invalid of ['0', '0.0', '0.000001', 'NaN', '-1.00', 0.75]) {
    assert.throws(() => decimalRateToNanos(invalid), /INVALID_PRICE/);
  }
});
test('documented maximums require exactly 103.2192 modeled AIC', async () => {
  const p = loadOfflineProfile(SNAPSHOT, NOW);
  assert.equal(p.maximumReservationNanos, 103219200000n);
  const bound = await p.boundForRequest({model: MODEL, requestSha256: 'bound-to-request',
    body: JSON.parse(BODY)});
  assert.equal(bound.maxInputTokens, 1048576);
  assert.equal(bound.maxChargedOutputTokens, 1);
  assert.equal(bound.requestSha256, 'bound-to-request');
});
for (const invalid of [
  {now: new Date('2026-10-25T00:00:00Z')},
  {now: new Date('2026-10-23T23:59:59Z')},
  {snapshot: {...SNAPSHOT, valid_until: '2027-01-01T00:00:00Z'}},
  {snapshot: {...SNAPSHOT, scope: 'LIVE_APPROVED'}},
  {snapshot: {...SNAPSHOT, service_tier: 'priority'}},
  {snapshot: {...SNAPSHOT, input_token_limit: NaN}},
]) {
  test('stale, invalid or broader price profile fails closed ' + JSON.stringify(invalid), () => {
    assert.throws(() => loadOfflineProfile(invalid.snapshot || SNAPSHOT, invalid.now || NOW));
  });
}
test('invalid price profile creates no runtime budget state', t => {
  const database = temp(t);
  assert.throws(() => createOfflineGateway({database, runId: 'offline', snapshot: SNAPSHOT,
    now: new Date('2027-01-01T00:00:00Z')}));
  assert.equal(fs.existsSync(database), false);
});
test('real price and bound are connected: 10-AIC preflight rejects before forwarding', async t => {
  const gateway = await start({database: temp(t), runId: 'offline-real-profile'});
  t.after(() => gateway.close());
  const res = await call(gateway);
  const text = await res.text();
  assert.equal(res.status, 400);
  assert.equal(JSON.parse(text).error, 'CREDIT_CAP_EXHAUSTED');
  assert.equal(text.includes('DO_NOT_LOG_TEST_PRIVATE_PAYLOAD'), false);
  assert.equal(gateway.forwardedCalls(), 0);
  assert.equal(gateway.ledger.snapshot().requests, 0);
});
test('developer and independent reviewer share the same persistent budget', async t => {
  const gateway = await start({database: temp(t), runId: 'offline-shared', testDependencies: fixtureDependencies()});
  t.after(() => gateway.close());
  assert.equal((await call(gateway, 'developer')).status, 200);
  assert.equal((await call(gateway, 'reviewer')).status, 200);
  assert.equal((await call(gateway, 'developer')).status, 400);
  assert.equal(gateway.ledger.snapshot().used, '10000000000');
  assert.equal(gateway.forwardedCalls(), 2);
});
test('restart cannot reset spent credits or change run identity', async t => {
  const database = temp(t);
  let gateway = await start({database, runId: 'same-run', testDependencies: fixtureDependencies()});
  await call(gateway, 'developer'); await call(gateway, 'reviewer'); await gateway.close();
  gateway = await start({database, runId: 'same-run', testDependencies: fixtureDependencies()});
  t.after(() => gateway.close());
  assert.equal((await call(gateway)).status, 400);
  assert.equal(gateway.forwardedCalls(), 0);
  assert.throws(() => new PersistentCreditLedger(database, 10000000000n, 12, 'new-run'), /CONFIG_MISMATCH/);
});
test('unknown role and untrusted token headers cannot bypass the ledger', async t => {
  const gateway = await start({database: temp(t), runId: 'offline-roles'});
  t.after(() => gateway.close());
  assert.equal((await call(gateway, 'bypass')).status, 403);
  const res = await fetch(gateway.origin + URL, {method: 'POST', body: BODY,
    headers: {'x-twf-role': 'developer', 'x-input-tokens': '1', 'x-live-approved': 'true'}});
  assert.equal(res.status, 400); assert.equal(gateway.forwardedCalls(), 0);
});
test('documented model limits cannot be increased by request configuration', async t => {
  const gateway = await start({database: temp(t), runId: 'offline-output'});
  t.after(() => gateway.close());
  const body = JSON.parse(BODY); body.generationConfig.maxOutputTokens = 65537;
  assert.equal(JSON.parse(await (await call(gateway, 'developer', JSON.stringify(body))).text()).error,
    'MODEL_LIMIT_EXCEEDED');
  assert.equal(gateway.forwardedCalls(), 0);
});
test('a lost in-flight lease remains reserved after reopening the database', t => {
  const database = temp(t);
  let ledger = new PersistentCreditLedger(database, 10n, 12, 'lost');
  ledger.reserve(7n); ledger.close();
  ledger = new PersistentCreditLedger(database, 10n, 12, 'lost');
  assert.equal(ledger.snapshot().reserved, '7');
  assert.throws(() => ledger.reserve(4n), /CREDIT_CAP_EXHAUSTED/); ledger.close();
});
test('invalid settlement halts durably and never releases an uncertain reservation', t => {
  const database = temp(t);
  let ledger = new PersistentCreditLedger(database, 10n, 12, 'halt');
  const lease = ledger.reserve(7n);
  assert.throws(() => ledger.settle(lease, 8n), /USAGE_EXCEEDS_RESERVATION/); ledger.close();
  ledger = new PersistentCreditLedger(database, 10n, 12, 'halt');
  assert.equal(ledger.snapshot().reserved, '7'); assert.equal(ledger.snapshot().halted, true);
  assert.throws(() => ledger.reserve(1n), /LEDGER_HALTED/); ledger.close();
});
test('no configuration can lift this offline candidate above the existing 10-AIC cap', t => {
  assert.throws(() => new PersistentCreditLedger(temp(t), 10000000001n, 12, 'wrong'), /INVALID_PERSISTENT_CONFIG/);
});
test('separate worker processes cannot reserve the same remaining budget', async t => {
  const database = temp(t);
  new PersistentCreditLedger(database, 10n, 12, 'workers').close();
  const moduleFile = path.resolve(__dirname, '../runtime/persistent_credit_ledger.cjs');
  const code = "const {PersistentCreditLedger}=require(process.argv[1]);const l=new PersistentCreditLedger(process.argv[2],10n,12,'workers');try{l.reserve(6n);process.stdout.write('RESERVED');}catch(e){process.stdout.write(e.code||e.message);}finally{l.close();}";
  const results = await Promise.all(Array.from({length: 6}, () => new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ['-e', code, moduleFile, database], {stdio: ['ignore', 'pipe', 'pipe']});
    let stdout = ''; let stderr = '';
    child.stdout.on('data', chunk => {stdout += chunk;}); child.stderr.on('data', chunk => {stderr += chunk;});
    child.on('error', reject);
    child.on('exit', status => status === 0 ? resolve(stdout) : reject(new Error(stderr)));
  })));
  assert.equal(results.filter(value => value === 'RESERVED').length, 1);
  assert.equal(results.filter(value => value === 'CREDIT_CAP_EXHAUSTED').length, 5);
  const ledger = new PersistentCreditLedger(database, 10n, 12, 'workers');
  assert.equal(ledger.snapshot().reserved, '6'); ledger.close();
});
test('health explicitly reports no live authorization', async t => {
  const gateway = await start({database: temp(t), runId: 'health'});
  t.after(() => gateway.close());
  const response = await fetch(gateway.origin + '/health');
  assert.deepEqual(await response.json(), {mode: 'OFFLINE_ONLY', liveAuthorized: false});
});
test('request output bound includes thinking and does not reserve the full model output window', async () => {
  const profile = loadOfflineProfile(SNAPSHOT, NOW);
  for (const output of [1, 512, 2048, 65536]) {
    const body = JSON.parse(BODY); body.generationConfig.maxOutputTokens = output;
    const bound = await profile.boundForRequest({model: MODEL, body, requestSha256: 'exact-request'});
    assert.equal(bound.maxChargedOutputTokens, output);
    assert.equal(bound.maxInputTokens, 1048576);
  }
});
test('2048-token output requires an independently certified input bound of at most 123093', () => {
  const result = inspectRequestBudget(SNAPSHOT, 2048, 10000000000n, NOW);
  assert.equal(result.reservationNanocredits, '79411200000');
  assert.equal(result.requiredInputCeilingToFit, '123093');
  const rate = loadOfflineProfile(SNAPSHOT, NOW).catalog.get(MODEL);
  const threshold = BigInt(result.requiredInputCeilingToFit);
  assert.ok(threshold * rate.inputNanosPerToken + 2048n * rate.outputNanosPerToken <= 10000000000n);
  assert.ok((threshold + 1n) * rate.inputNanosPerToken + 2048n * rate.outputNanosPerToken > 10000000000n);
  assert.equal(result.requestSpecificInputProofAvailable, false);
  assert.equal(result.admissionGranted, false);
});
test('one output token still cannot fit the unverified model-ceiling input bound under 10 AIC', () => {
  const result = inspectRequestBudget(SNAPSHOT, 1, 10000000000n, NOW);
  assert.equal(result.reservationNanocredits, '78643575000');
  assert.equal(result.status, 'BLOCKED_NO_VERIFIED_SMALL_INPUT_BOUND');
  assert.equal(result.admissionGranted, false);
});
test('budget thresholds use remaining credits and do not silently raise the cap', () => {
  const full = inspectRequestBudget(SNAPSHOT, 512, 10000000000n, NOW);
  const half = inspectRequestBudget(SNAPSHOT, 512, 5000000000n, NOW);
  assert.ok(BigInt(half.requiredInputCeilingToFit) < BigInt(full.requiredInputCeilingToFit));
  assert.throws(() => inspectRequestBudget(SNAPSHOT, 512, 10000000001n, NOW), /INVALID_REQUEST_BUDGET/);
  assert.throws(() => inspectRequestBudget(SNAPSHOT, 65537, 10000000000n, NOW), /INVALID_REQUEST_BUDGET/);
});
test('client token estimates cannot replace the unresolved input proof', async t => {
  const gateway = await start({database: temp(t), runId: 'unverified-input'});
  t.after(() => gateway.close());
  const res = await fetch(gateway.origin + URL, {method: 'POST', body: BODY,
    headers: {'x-twf-role': 'developer', 'x-count-tokens': '1', 'x-input-bound': '1', 'x-sdk-supported': 'true'}});
  assert.equal(res.status, 400);
  assert.equal(gateway.forwardedCalls(), 0);
});
