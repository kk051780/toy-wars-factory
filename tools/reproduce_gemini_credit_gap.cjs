#!/usr/bin/env node
'use strict';
// Offline only. Load hash-pinned upstream modules without network or credentials.
// Usage: node tools/reproduce_gemini_credit_gap.cjs /path/to/gh-aw-firewall-v0.28.70
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');

const PINNED_BLOBS = {
  "containers/api-proxy/guards/ai-credits-guard.js": "9f1b608685ae1edc8b5962e1e6f5999dce1e7572",
  "containers/api-proxy/ai-credits-pricing.js": "49b52bbcfe2b4bf9e460ae7343c434a7fcd015da",
  "containers/api-proxy/models-dev-catalog.js": "de65bb5480b63e0a5a8d76a065297f14bfaba1bc",
  "containers/api-proxy/models.dev.catalog.json": "7aadc2a15168959d020df4252b650337536e1c1d",
  "containers/api-proxy/runtime-model-catalog.js": "a3a9315d001bb69239f59b802661ea066efbcb18",
  "containers/api-proxy/provider-pricing-overlays.js": "f3a33ba0d96938d10c1c4d90dd2c7757f6f3d9b5",
  "containers/api-proxy/model-pricing-catalog.js": "f9a8ea999e785e569939702cfac11b01db0d4843",
  "containers/api-proxy/guards/guard-utils.js": "c410bee62f160b8791b7244f2004c7699a6d47d2",
  "containers/api-proxy/guards/steering-thresholds.js": "910d69c77abd249dec9e2324e1c9a951d41f91db",
  "containers/api-proxy/provider-names.js": "ddc3e967d84eb3ad56d084a47e25a423a983d9e9",
  "containers/api-proxy/proxy-guards.js": "f50f31b6751c03221d7fa9aae2e3f87a0327d1d4"
};

function loadPinnedFirewall(upstreamRoot, options = {}) {
  const modules = new Map();
  const files = new Map();
  for (const [name, expected] of Object.entries({...PINNED_BLOBS, ...options.extraPins})) {
    const bytes = fs.readFileSync(path.join(upstreamRoot, name));
    const actual = crypto.createHash('sha1')
      .update(Buffer.from('blob ' + bytes.length + '\0')).update(bytes).digest('hex');
    assert.equal(actual, expected, 'Upstream blob mismatch: ' + name);
    files.set(name, bytes.toString('utf8'));
  }
  for (const [name, content] of Object.entries(options.sourceOverrides || {})) files.set(name, content);
  // Pricing is original tagged code. Logging alone is stubbed; runtime env is isolated.
  const context = vm.createContext({Buffer, process: {env: {AWF_MAX_AI_CREDITS: '10'}}});
  function load(name) {
    if (Object.hasOwn(options.moduleStubs || {}, name)) return options.moduleStubs[name];
    if (name === 'containers/api-proxy/logging.js') {
      return {logRequest() {}, sanitizeForLog(value) { return value; }};
    }
    assert.ok(files.has(name), 'Unpinned dependency: ' + name);
    if (modules.has(name)) return modules.get(name).exports;
    const module = {exports: {}};
    modules.set(name, module);
    if (name.endsWith('.json')) {
      module.exports = JSON.parse(files.get(name));
      return module.exports;
    }
    function localRequire(request) {
      if (name === 'containers/api-proxy/twf-gemini-budget-guard.js' && request === 'node:crypto') {
        return require('node:crypto');
      }
      assert.ok(request.startsWith('.'), 'External dependency disallowed: ' + request);
      let resolved = path.posix.normalize(path.posix.join(path.posix.dirname(name), request));
      if (!resolved.endsWith('.js') && !resolved.endsWith('.json')) resolved += '.js';
      return load(resolved);
    }
    const factory = vm.runInContext(
      '(function(exports, require, module) {\n' + files.get(name) + '\n})',
      context, {filename: name, timeout: 2000});
    factory(module.exports, localRequire, module);
    return module.exports;
  }
  return {load, files, context};
}

function reproduce(upstreamRoot) {
  const {load, files, context} = loadPinnedFirewall(upstreamRoot);
  const proxySource = files.get('containers/api-proxy/proxy-guards.js');
  const extractorSource = proxySource.slice(
    proxySource.indexOf('function extractModelFromBody(body) {'),
    proxySource.indexOf('\n/**', proxySource.indexOf('function extractModelFromBody(body) {')));
  const extractModel = vm.runInContext('(' + extractorSource + ')', context);
  const guard = load('containers/api-proxy/guards/ai-credits-guard.js');
  const model = 'gemini-3.8-flash';
  const nativeBody = Buffer.from(JSON.stringify({contents: []}));
  const bodyModel = extractModel(nativeBody);
  assert.equal(bodyModel, null);
  assert.equal(guard.checkUnknownModelRejection(bodyModel, 'gemini'), null);
  assert.equal(guard.isModelPriceable(model, 'gemini'), false);
  const firstUsage = {input_tokens: 15029, output_tokens: 201,
    cache_read_tokens: 0, cache_write_tokens: 0};
  const accounted = guard.applyAiCreditsUsage(firstUsage, model, 'gemini');
  assert.equal(accounted, null);
  const creditState = guard.getAiCreditsBlockState();
  assert.equal(creditState.totalAiCredits, 0);
  assert.equal(creditState.maxExceeded, false);
  assert.equal(guard.checkUnknownModelRejection(model, 'gemini').rejected, true);
  // Positive control: a priced model must accumulate a nonzero credit amount.
  const control = guard.applyAiCreditsUsage(firstUsage, 'gemini-3.5-flash', 'gemini');
  assert.ok(control.totalAiCredits > 0);
  return {
    status: 'OFFLINE_REPRODUCED_UNPRICED_NATIVE_MODEL_GAP',
    upstream: 'github/gh-aw-firewall@v0.28.70',
    verified_upstream_blobs: files.size,
    provider_calls: 0, credentials_read: false,
    native_body_model: bodyModel, unknown_model_admission: 'NOT_REJECTED',
    unpriced_model: model, pricing_result: accounted,
    internal_credit_total_after_usage: creditState.totalAiCredits,
    internal_credit_cap_exceeded: creditState.maxExceeded,
    explicit_named_model_admission: 'REJECTED',
    priced_model_positive_control: 'PASS',
    mitigation_deployed: false,
    note: 'This reproduces the tagged source failure mode; it does not attest deployed container bytes or actual billing.'
  };
}

if (require.main === module) {
  try {
    assert.ok(process.argv[2], 'Provide the offline upstream checkout path.');
    console.log(JSON.stringify(reproduce(path.resolve(process.argv[2])), null, 2));
  } catch (error) {
    console.error('OFFLINE_REPRODUCTION_FAILED: ' + error.message);
    process.exitCode = 1;
  }
}
module.exports = {reproduce, loadPinnedFirewall, PINNED_BLOBS};
