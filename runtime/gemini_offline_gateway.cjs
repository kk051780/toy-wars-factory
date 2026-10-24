'use strict';
// Offline connection only. This module contains no provider URL transport or credential reads.
const http = require('node:http');
const fs = require('node:fs');
const {GuardError, createBoundedRunner} = require('./gemini_budget_guard.cjs');
const {PersistentCreditLedger} = require('./persistent_credit_ledger.cjs');

function decimalRateToNanos(value) {
  // USD / 1M tokens divided by $0.01/AIC, multiplied by 1e9 nanocredits/AIC.
  if (typeof value !== 'string' || !/^\d+\.\d{1,5}$/.test(value)) throw new GuardError('INVALID_PRICE');
  const [whole, decimals] = value.split('.');
  const result = BigInt(whole) * 100000n + BigInt(decimals.padEnd(5, '0'));
  if (result <= 0n) throw new GuardError('INVALID_PRICE');
  return result;
}
function loadOfflineProfile(snapshot, now = new Date()) {
  if (snapshot.scope !== 'OFFLINE_PREFLIGHT_ONLY_NO_LIVE_AUTHORIZATION' ||
      snapshot.model !== 'gemini-3.8-flash' || snapshot.aic_usd !== '0.01' ||
      snapshot.service_tier !== 'standard' || snapshot.modality !== 'text_only') {
    throw new GuardError('UNSUPPORTED_PRICE_PROFILE');
  }
  const reviewed = Date.parse(snapshot.reviewed_on + 'T00:00:00Z');
  const expires = Date.parse(snapshot.valid_until);
  if (!Number.isFinite(+now) || !Number.isFinite(reviewed) || !Number.isFinite(expires) ||
      +now < reviewed || +now >= expires || expires - reviewed > 86400000 * 2) {
    throw new GuardError('EXPIRED_OR_INVALID_PRICE_SNAPSHOT');
  }
  for (const value of [snapshot.input_token_limit, snapshot.output_token_limit]) {
    if (!Number.isSafeInteger(value) || value <= 0) throw new GuardError('INVALID_MODEL_LIMIT');
  }
  const rate = Object.freeze({approved: true, evidence: snapshot.pricing_url,
    approvalScope: 'OFFLINE_PREFLIGHT_ONLY',
    inputNanosPerToken: decimalRateToNanos(snapshot.input_usd_per_million),
    outputNanosPerToken: decimalRateToNanos(snapshot.output_usd_per_million_including_thinking)});
  const catalog = new Map([[snapshot.model, rate]]);
  const inputLimit = snapshot.input_token_limit;
  const outputLimit = snapshot.output_token_limit;
  const model = snapshot.model;
  const boundForRequest = async spec => {
    if (spec.model !== model || spec.body.generationConfig.maxOutputTokens > outputLimit) {
      throw new GuardError('MODEL_LIMIT_EXCEEDED');
    }
    // CountTokens is not promoted into an upper-bound proof. Reserve the full documented limits.
    return {kind: 'HOST_VERIFIED_UPPER_BOUND', requestSha256: spec.requestSha256,
      maxInputTokens: inputLimit, maxChargedOutputTokens: outputLimit};
  };
  return {catalog, boundForRequest,
    maximumReservationNanos: BigInt(inputLimit) * rate.inputNanosPerToken + BigInt(outputLimit) * rate.outputNanosPerToken};
}

function createOfflineGateway({database, runId, snapshot, now = new Date(), testDependencies} = {}) {
  if (!database || !runId) throw new GuardError('MISSING_OFFLINE_RUNTIME_CONFIG');
  const profile = loadOfflineProfile(snapshot, now);
  const ledger = new PersistentCreditLedger(database, 10000000000n, 12, runId);
  let forwards = 0;
  const run = createBoundedRunner({ledger,
    catalog: testDependencies?.catalog || profile.catalog,
    boundForRequest: testDependencies?.boundForRequest || profile.boundForRequest,
    transport: async spec => {
      forwards++;
      if (!testDependencies?.transport) throw new GuardError('LIVE_TRANSPORT_NOT_AUTHORIZED');
      return testDependencies.transport(spec);
    }});
  const server = http.createServer(async (req, res) => {
    if (req.method === 'GET' && req.url === '/health') {
      res.writeHead(200, {'Content-Type': 'application/json'});
      return res.end(JSON.stringify({mode: 'OFFLINE_ONLY', liveAuthorized: false}));
    }
    const role = req.headers['x-twf-role'];
    if (!['developer', 'reviewer'].includes(role)) {
      res.writeHead(403); return res.end('{"error":"UNKNOWN_ROLE"}');
    }
    try {
      const chunks = []; let length = 0;
      for await (const chunk of req) {
        length += chunk.length;
        if (length > 131072) throw new GuardError('REQUEST_TOO_LARGE');
        chunks.push(chunk);
      }
      const value = await run({method: req.method, url: req.url, body: Buffer.concat(chunks)});
      res.writeHead(200, {'Content-Type': 'application/json'}); res.end(JSON.stringify(value));
    } catch (error) {
      res.writeHead(400, {'Content-Type': 'application/json'});
      res.end(JSON.stringify({error: error instanceof GuardError ? error.code : 'OFFLINE_RUNTIME_FAILURE', retryable: false}));
    }
  });
  return {server, ledger, profile, forwardedCalls: () => forwards,
    close: async () => {server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); ledger.close();}};
}

if (require.main === module) {
  // This entry point supports offline validation only; live mode cannot be enabled by an env flag.
  if (process.argv[2] !== '--offline' || !process.argv[3]) throw new GuardError('OFFLINE_ARGUMENT_REQUIRED');
  const path = require('node:path');
  const snapshot = JSON.parse(fs.readFileSync(path.join(__dirname, 'gemini_price_snapshot.json'), 'utf8'));
  const gateway = createOfflineGateway({database: process.argv[3], runId: 'offline-candidate', snapshot});
  gateway.server.listen(8080, '127.0.0.1', () => console.log('OFFLINE_GATEWAY_READY liveAuthorized=false'));
}
module.exports = {decimalRateToNanos, loadOfflineProfile, createOfflineGateway};
