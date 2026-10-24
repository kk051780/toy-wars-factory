'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const {once} = require('node:events');
const {GuardError, resolveNativeRequest, validateNativeAdmission, CreditLedger,
  createBoundedRunner} = require('../runtime/gemini_budget_guard.cjs');

const MODEL = 'fixture-text-model';
function request(overrides = {}) {
  return {method: 'POST', url: '/v1beta/models/' + MODEL + ':generateContent',
    body: Buffer.from(JSON.stringify({contents: [{role: 'user', parts: [{text: 'hello'}]}],
      generationConfig: {maxOutputTokens: 10, candidateCount: 1}})), ...overrides};
}
function response(input = 10, output = 10, thoughts = 0) {
  return {modelVersion: MODEL, usageMetadata: {promptTokenCount: input,
    candidatesTokenCount: output, thoughtsTokenCount: thoughts,
    totalTokenCount: input + output + thoughts}};
}
function harness(options = {}) {
  const ledger = new CreditLedger(options.cap ?? 10000n, options.maxRequests ?? 12);
  const calls = {bound: 0, forward: 0};
  const run = createBoundedRunner({ledger,
    catalog: options.catalog ?? new Map([[MODEL, {approved: true, evidence: 'test-fixture://synthetic-rates',
      inputNanosPerToken: 100n, outputNanosPerToken: 100n}]]),
    boundForRequest: async spec => {
      calls.bound++;
      return options.bound ? options.bound(spec) : {kind: 'HOST_VERIFIED_UPPER_BOUND',
        requestSha256: spec.requestSha256, maxInputTokens: 10, maxChargedOutputTokens: 10};
    },
    transport: async spec => {calls.forward++; return options.transport ? options.transport(spec) : response();},
  });
  return {ledger, calls, run};
}

test('native URL supplies the model, including the streaming URL', () => {
  assert.equal(resolveNativeRequest('POST', request().url, request().body).model, MODEL);
  assert.equal(resolveNativeRequest('POST', '/v1/models/' + MODEL + ':streamGenerateContent?alt=sse',
    request().body).action, 'streamGenerateContent');
  assert.equal(validateNativeAdmission(request(), request().body, () => false).error.type,
    'UNPRICED_NATIVE_MODEL');
});
for (const url of ['/v1beta/models/' + MODEL + ':batchGenerateContent',
  '/v1beta/models/../x:generateContent', '/v1beta/models/x%2Fy:generateContent',
  '/v1beta/models/x:generateContent?model=other', '//attacker/models/x:generateContent',
  'https://attacker/v1beta/models/x:generateContent', '/v1beta/models/x:generateContent#tail']) {
  test('reject ambiguous/unsupported native URL ' + url, () => {
    assert.throws(() => resolveNativeRequest('POST', url, request().body), GuardError);
  });
}
test('native model cannot be replaced by a cheap body model', () => {
  const body = Buffer.from(JSON.stringify({model: 'cheaper-model'}));
  assert.throws(() => resolveNativeRequest('POST', request().url, body), /NATIVE_BODY_MODEL_MISMATCH/);
});
test('malformed body, array and non-POST fail closed', () => {
  for (const body of [Buffer.from('{'), Buffer.from('[]'), Buffer.from('null')]) {
    assert.throws(() => resolveNativeRequest('POST', request().url, body), /INVALID_JSON_BODY/);
  }
  assert.throws(() => resolveNativeRequest('PUT', request().url, request().body), /INVALID_NATIVE_REQUEST/);
});
test('unpriced live model is rejected before token bounding or forwarding', async () => {
  const h = harness({catalog: new Map()});
  await assert.rejects(h.run(request({url: '/v1beta/models/gemini-3.8-flash:generateContent'})), /UNPRICED/);
  assert.deepEqual(h.calls, {bound: 0, forward: 0});
});
test('price approval and price evidence are both required', async () => {
  for (const rate of [{approved: false}, {approved: true}]) {
    const h = harness({catalog: new Map([[MODEL, rate]])});
    await assert.rejects(h.run(request()), /UNPRICED/);
    assert.equal(h.calls.forward, 0);
  }
});
test('no caller-supplied or stale token bound is accepted', async () => {
  for (const bound of [() => null, () => ({kind: 'HOST_VERIFIED_UPPER_BOUND', requestSha256: 'stale'}),
    spec => ({requestSha256: spec.requestSha256, maxInputTokens: 1, maxChargedOutputTokens: 10})]) {
    const h = harness({bound});
    await assert.rejects(h.run(request()), /UNVERIFIED_REQUEST_BOUND/);
    assert.equal(h.calls.forward, 0);
  }
});
test('reserve before forwarding: a single request larger than the cap makes zero calls', async () => {
  const h = harness({cap: 1999n});
  await assert.rejects(h.run(request()), /CREDIT_CAP_EXHAUSTED/);
  assert.equal(h.calls.forward, 0);
});
test('exact cap succeeds, and repeated attempts cause no further transport calls', async () => {
  const h = harness();
  for (let i = 0; i < 5; i++) await h.run(request());
  for (let i = 0; i < 4; i++) await assert.rejects(h.run(request()), /CREDIT_CAP_EXHAUSTED/);
  assert.equal(h.calls.forward, 5);
  assert.equal(h.calls.bound, 5);
  assert.equal(h.ledger.snapshot().used, '10000');
});
test('concurrent requests cannot reserve the same remaining credits', async () => {
  let finish;
  const wait = new Promise(resolve => {finish = resolve;});
  const h = harness({cap: 2000n, transport: async () => {await wait; return response();}});
  const first = h.run(request());
  await new Promise(resolve => setImmediate(resolve));
  await assert.rejects(h.run(request()), /CREDIT_CAP_EXHAUSTED/);
  assert.equal(h.calls.forward, 1);
  assert.equal(h.ledger.snapshot().reserved, '2000');
  finish(); await first;
  assert.equal(h.ledger.snapshot().used, '2000');
});
test('request cap is terminal even with budget remaining', async () => {
  const h = harness({maxRequests: 1});
  await h.run(request());
  await assert.rejects(h.run(request()), /REQUEST_CAP_EXHAUSTED/);
  assert.equal(h.calls.forward, 1);
});
test('only a complete successful response releases unused reservation', async () => {
  const h = harness({transport: async () => response(4, 3)});
  await h.run(request());
  assert.equal(h.ledger.snapshot().used, '700');
  assert.equal(h.ledger.snapshot().reserved, '0');
});
test('thinking tokens count against the charged output bound', async () => {
  const h = harness({transport: async () => response(10, 4, 6)});
  await h.run(request());
  assert.equal(h.ledger.snapshot().used, '2000');
});
for (const [label, value] of [['missing usage', {}], ['negative usage', response(-1)],
  ['output above bound', response(10, 11)], ['input above bound', response(11, 1)],
  ['missing total', {usageMetadata: {promptTokenCount: 10, candidatesTokenCount: 1}}],
  ['contradictory total', {usageMetadata: {promptTokenCount: 10, candidatesTokenCount: 1, totalTokenCount: 50}}],
  ['routed model changed', {...response(), modelVersion: 'different'}]]) {
  test('uncertain response halts and retains reservation: ' + label, async () => {
    const h = harness({transport: async () => value});
    await assert.rejects(h.run(request()), GuardError);
    await assert.rejects(h.run(request()), /LEDGER_HALTED/);
    assert.equal(h.calls.forward, 1);
    assert.equal(h.ledger.snapshot().reserved, '2000');
  });
}
test('timeout is not retried or refunded', async () => {
  const h = harness({transport: async () => {throw new Error('timeout');}});
  await assert.rejects(h.run(request()), /timeout/);
  await assert.rejects(h.run(request()), /LEDGER_HALTED/);
  assert.equal(h.calls.forward, 1);
  assert.equal(h.ledger.snapshot().reserved, '2000');
});
test('unsupported costly features cannot reach transport', async () => {
  for (const extra of [{tools: []}, {cachedContent: 'cached'}, {generationConfig: {maxOutputTokens: 10, candidateCount: 2}},
    {contents: [{parts: [{inlineData: {data: 'unbounded'}}]}]}]) {
    const body = {...JSON.parse(request().body), ...extra};
    const h = harness();
    await assert.rejects(h.run(request({body: Buffer.from(JSON.stringify(body))})), GuardError);
    assert.equal(h.calls.forward, 0);
  }
});
test('external mutation cannot change the request after counting starts', async () => {
  let finish;
  const h = harness({bound: spec => new Promise(resolve => {finish = () => resolve({kind: 'HOST_VERIFIED_UPPER_BOUND',
    requestSha256: spec.requestSha256, maxInputTokens: 10, maxChargedOutputTokens: 10});}),
    transport: async spec => {assert.equal(JSON.parse(spec.body).contents[0].parts[0].text, 'hello'); return response();}});
  const input = request();
  const pending = h.run(input);
  input.body.fill(32);
  finish(); await pending;
});
test('closed leases, negative charges and inexact integers are rejected', () => {
  const ledger = new CreditLedger(10n);
  const lease = ledger.reserve(10n);
  ledger.settle(lease, 5n);
  assert.throws(() => ledger.settle(lease, 5n), /INVALID_OR_CLOSED_LEASE/);
  assert.throws(() => new CreditLedger(1.1), /INVALID_CREDIT_CAP/);
  assert.throws(() => new CreditLedger(1n, NaN), /INVALID_REQUEST_CAP/);
});
test('real loopback server observes zero requests after the exact cap', async t => {
  let received = 0;
  const server = http.createServer((req, res) => {
    assert.equal(req.socket.remoteAddress, '127.0.0.1');
    received++;
    req.resume();
    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify(response()));
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  t.after(() => {server.closeAllConnections(); server.close();});
  const origin = 'http://127.0.0.1:' + server.address().port;
  const h = harness({cap: 4000n, transport: async spec => {
    const res = await fetch(origin + spec.url, {method: spec.method, body: spec.body});
    return res.json();
  }});
  await h.run(request()); await h.run(request());
  for (let i = 0; i < 3; i++) await assert.rejects(h.run(request()), /CREDIT_CAP_EXHAUSTED/);
  assert.equal(received, 2);
});
