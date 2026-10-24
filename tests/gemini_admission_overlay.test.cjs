'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const {once} = require('node:events');
const {spawnSync} = require('node:child_process');
const {loadPinnedFirewall, reproduce} = require('../tools/reproduce_gemini_credit_gap.cjs');

const UPSTREAM = process.env.TWF_AWF_ROOT;
const ROOT = path.resolve(__dirname, '..');
const COMMON = 'containers/api-proxy/guards/common-guard-checks.js';
const COMMON_PIN = '1adf5f6900b8459496a3703d9fc41fbb481c74ec';
function fixture(t, patched = true, denyModel = false) {
  const output = fs.mkdtempSync(path.join(os.tmpdir(), 'twf-overlay-'));
  t.after(() => fs.rmSync(output, {recursive: true, force: true}));
  const build = spawnSync('python3', ['tools/build_gemini_admission_overlay.py',
    '--upstream', UPSTREAM, '--output', output], {cwd: ROOT, encoding: 'utf8'});
  assert.equal(build.status, 0, build.stderr);
  const noops = {gaugeDec() {}, increment() {}, observe() {}};
  const nullBlock = () => null;
  const error = () => ({error: 'preserved_guard'});
  const moduleStubs = {
    'containers/api-proxy/metrics.js': noops,
    'containers/api-proxy/blocked-request-diagnostics.js': {writeBlockedRequestDiag() {}},
    'containers/api-proxy/otel.js': {endSpan() {}},
    'containers/api-proxy/guards/max-runs-guard.js': {getMaxRunsBlockState: nullBlock, buildMaxRunsExceededError: error},
    'containers/api-proxy/guards/max-cache-misses-guard.js': {getMaxCacheMissesBlockState: nullBlock, buildMaxCacheMissesExceededError: error},
    'containers/api-proxy/guards/max-permission-denied-guard.js': {getPermissionDeniedBlockState: nullBlock, buildPermissionDeniedLimitError: error},
    'containers/api-proxy/guards/max-model-multiplier-guard.js': {getModelMultiplierCapBlockState: nullBlock, buildModelMultiplierCapError: error},
    'containers/api-proxy/guards/retired-model-guard.js': {getRetiredModelBlockState: nullBlock, buildRetiredModelError: error},
    'containers/api-proxy/guards/model-policy-guard.js': {getModelPolicyBlockState: () => denyModel ? {reason: 'fixture deny'} : null, buildModelPolicyError: error},
  };
  const sourceOverrides = patched ? {
    'containers/api-proxy/proxy-guards.js': fs.readFileSync(path.join(output, 'proxy-guards.js'), 'utf8'),
    'containers/api-proxy/twf-gemini-budget-guard.js': fs.readFileSync(path.join(output, 'twf-gemini-budget-guard.js'), 'utf8'),
  } : {};
  const loader = loadPinnedFirewall(UPSTREAM, {extraPins: {[COMMON]: COMMON_PIN}, sourceOverrides, moduleStubs});
  return {proxy: loader.load('containers/api-proxy/proxy-guards.js'),
    credits: loader.load('containers/api-proxy/guards/ai-credits-guard.js'), output};
}
function check(f, model = 'gemini-3.8-flash', body = {contents: []}, provider = 'gemini') {
  let status;
  let result;
  const req = {method: 'POST', url: '/v1beta/models/' + model + ':generateContent'};
  const blocked = f.proxy.enforceGuards({req, provider, body: Buffer.from(JSON.stringify(body)),
    res: {writeHead(code) {status = code;}, end(value) {result = JSON.parse(value);}},
    requestId: 'offline-test', startTime: Date.now(), span: {}, inboundBytes: 2});
  return {blocked, status, result};
}

test('original pinned runtime still reproduces the incident before the patch', {skip: !UPSTREAM}, t => {
  assert.equal(reproduce(UPSTREAM).internal_credit_total_after_usage, 0);
  assert.equal(check(fixture(t, false)).blocked, false);
});
test('patched actual admission blocks the unpriced native model', {skip: !UPSTREAM}, t => {
  const result = check(fixture(t));
  assert.equal(result.blocked, true);
  assert.equal(result.status, 400);
  assert.equal(result.result.error.type, 'UNPRICED_NATIVE_MODEL');
  assert.equal(result.result.error.retryable, false);
});
test('a priced native model reaches the original guard descriptors', {skip: !UPSTREAM}, t => {
  assert.equal(check(fixture(t), 'gemini-3.5-flash').blocked, false);
});
test('native/body mismatch is rejected before reaching upstream', {skip: !UPSTREAM}, t => {
  const result = check(fixture(t), 'gemini-3.5-flash', {model: 'gemini-3-flash'});
  assert.equal(result.blocked, true);
  assert.equal(result.result.error.type, 'NATIVE_BODY_MODEL_MISMATCH');
});
test('original model-policy rejection remains active', {skip: !UPSTREAM}, t => {
  const result = check(fixture(t, true, true), 'gemini-3.5-flash');
  assert.equal(result.blocked, true);
  assert.equal(result.status, 403);
  assert.equal(result.result.error, 'preserved_guard');
});
test('original exhausted-credit rejection remains active', {skip: !UPSTREAM}, t => {
  const f = fixture(t);
  f.credits.applyAiCreditsUsage({input_tokens: 100000, output_tokens: 0}, 'gemini-3.5-flash', 'gemini');
  const result = check(f, 'gemini-3.5-flash');
  assert.equal(result.blocked, true);
  assert.equal(result.status, 403);
  assert.equal(result.result.error.type, 'ai_credits_limit_exceeded');
});
test('non-Gemini admission retains original behavior', {skip: !UPSTREAM}, t => {
  const body = {model: 'claude-sonnet-4'};
  assert.equal(check(fixture(t), 'unused', body, 'anthropic').blocked,
    check(fixture(t, false), 'unused', body, 'anthropic').blocked);
});
test('unexpected upstream revision is rejected without producing an overlay', {skip: !UPSTREAM}, t => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'twf-wrong-pin-'));
  t.after(() => fs.rmSync(temp, {recursive: true, force: true}));
  const wrongUpstream = path.join(temp, 'upstream');
  fs.mkdirSync(path.join(wrongUpstream, 'containers/api-proxy'), {recursive: true});
  fs.writeFileSync(path.join(wrongUpstream, 'containers/api-proxy/proxy-guards.js'), '// changed upstream');
  const destination = path.join(temp, 'output');
  const result = spawnSync('python3', ['tools/build_gemini_admission_overlay.py',
    '--upstream', wrongUpstream, '--output', destination], {cwd: ROOT, encoding: 'utf8'});
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /differs from the reviewed/);
  assert.equal(fs.existsSync(destination), false);
});
test('patched HTTP gate makes no loopback upstream calls for rejected native models', {skip: !UPSTREAM}, async t => {
  const f = fixture(t);
  let upstreamCalls = 0;
  const upstream = http.createServer((req, res) => {upstreamCalls++; req.resume(); res.end('{"ok":true}');});
  upstream.listen(0, '127.0.0.1'); await once(upstream, 'listening');
  const origin = 'http://127.0.0.1:' + upstream.address().port;
  const gate = http.createServer(async (req, res) => {
    const chunks = []; for await (const chunk of req) chunks.push(chunk);
    const body = Buffer.concat(chunks);
    const blocked = f.proxy.enforceGuards({req, res, body, provider: 'gemini',
      requestId: 'local-http', startTime: Date.now(), span: {}, inboundBytes: body.length});
    if (!blocked) {
      const response = await fetch(origin + req.url, {method: 'POST', body});
      res.end(await response.text());
    }
  });
  gate.listen(0, '127.0.0.1'); await once(gate, 'listening');
  t.after(() => {for (const server of [gate, upstream]) {server.closeAllConnections(); server.close();}});
  const base = 'http://127.0.0.1:' + gate.address().port;
  const rejected = await Promise.all(Array.from({length: 20}, () => fetch(base +
    '/v1beta/models/gemini-3.8-flash:generateContent', {method: 'POST', body: '{"contents":[]}'})));
  assert.ok(rejected.every(response => response.status === 400));
  assert.equal(upstreamCalls, 0);
  const accepted = await fetch(base + '/v1beta/models/gemini-3.5-flash:generateContent',
    {method: 'POST', body: '{"contents":[]}'});
  assert.equal(accepted.status, 200);
  assert.equal(upstreamCalls, 1);
});
