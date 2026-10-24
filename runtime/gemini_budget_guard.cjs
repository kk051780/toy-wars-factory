'use strict';
// Candidate only: no network implementation, credentials or approved live prices.
const crypto = require('node:crypto');

class GuardError extends Error {
  constructor(code) { super(code); this.code = code; this.retryable = false; }
}
function reject(code) { throw new GuardError(code); }
function integer(value, label, positive = false) {
  if (!Number.isSafeInteger(value) || value < (positive ? 1 : 0)) reject(label);
  return value;
}
function nanos(value, label) {
  if (typeof value !== 'bigint' || value <= 0n) reject(label);
  return value;
}

function resolveNativeRequest(method, url, bytes) {
  if (method !== 'POST' || typeof url !== 'string') reject('INVALID_NATIVE_REQUEST');
  if (/[\\%#]/.test(url)) reject('AMBIGUOUS_NATIVE_URL');
  const match = /^\/v1(?:beta)?\/models\/([A-Za-z0-9][A-Za-z0-9._-]{0,127}):(generateContent|streamGenerateContent|countTokens)(?:\?alt=sse)?$/.exec(url);
  if (!match || (url.includes('?') && match[2] !== 'streamGenerateContent')) {
    reject('UNSUPPORTED_NATIVE_URL');
  }
  let body;
  try { body = JSON.parse(Buffer.from(bytes).toString('utf8')); }
  catch { reject('INVALID_JSON_BODY'); }
  if (!body || Array.isArray(body) || typeof body !== 'object') reject('INVALID_JSON_BODY');
  if ('model' in body && body.model !== match[1] && body.model !== 'models/' + match[1]) {
    reject('NATIVE_BODY_MODEL_MISMATCH');
  }
  return {model: match[1], action: match[2], body};
}

function validateNativeAdmission(req, body, isPriceable) {
  try {
    const result = resolveNativeRequest(req.method, req.url, body);
    if (!isPriceable(result.model, 'gemini')) reject('UNPRICED_NATIVE_MODEL');
    return {ok: true, model: result.model};
  } catch (error) {
    if (!(error instanceof GuardError)) throw error;
    return {ok: false, error: {type: error.code, retryable: false}};
  }
}

class CreditLedger {
  #cap; #used = 0n; #reserved = 0n; #leases = new Map(); #requests = 0;
  #maxRequests; #halted = false;
  constructor(capNanos, maxRequests = 12) {
    this.#cap = nanos(capNanos, 'INVALID_CREDIT_CAP');
    this.#maxRequests = integer(maxRequests, 'INVALID_REQUEST_CAP', true);
  }
  reserve(amount) {
    nanos(amount, 'INVALID_RESERVATION');
    this.assertOpen();
    if (this.#used + this.#reserved + amount > this.#cap) reject('CREDIT_CAP_EXHAUSTED');
    const lease = Object.freeze({});
    this.#leases.set(lease, amount);
    this.#requests++;
    this.#reserved += amount;
    return lease;
  }
  settle(lease, actual) {
    if (!this.#leases.has(lease)) reject('INVALID_OR_CLOSED_LEASE');
    const reserved = this.#leases.get(lease);
    if (typeof actual !== 'bigint' || actual < 0n || actual > reserved) {
      this.halt(); // Keep the full reservation when the upper-bound contract fails.
      reject('USAGE_EXCEEDS_RESERVATION');
    }
    this.#leases.delete(lease);
    this.#reserved -= reserved;
    this.#used += actual;
  }
  halt() { this.#halted = true; }
  assertOpen() {
    if (this.#halted) reject('LEDGER_HALTED');
    if (this.#requests >= this.#maxRequests) reject('REQUEST_CAP_EXHAUSTED');
    if (this.#used + this.#reserved >= this.#cap) reject('CREDIT_CAP_EXHAUSTED');
  }
  snapshot() {
    return {cap: String(this.#cap), used: String(this.#used), reserved: String(this.#reserved),
      requests: this.#requests, halted: this.#halted};
  }
}

function deepFreeze(value) {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(deepFreeze);
    Object.freeze(value);
  }
  return value;
}

function createBoundedRunner({ledger, catalog, boundForRequest, transport}) {
  if (!(ledger instanceof CreditLedger) || !(catalog instanceof Map) ||
      typeof boundForRequest !== 'function' || typeof transport !== 'function') {
    reject('MISSING_TRUSTED_RUNTIME_DEPENDENCY');
  }
  // Copy the approved catalog so a concurrent caller cannot change rates in flight.
  const prices = new Map([...catalog].map(([model, rate]) => [model, Object.freeze({...rate})]));
  return async function run(input) {
    ledger.assertOpen();
    const method = input.method;
    const url = input.url;
    const bodyBytes = Buffer.from(input.body); // Bind counting and generation to one snapshot.
    const {model, action, body} = resolveNativeRequest(method, url, bodyBytes);
    if (action !== 'generateContent') reject('BOUNDED_RUNNER_NONSTREAM_ONLY');
    const rate = prices.get(model);
    if (!rate || rate.approved !== true || typeof rate.evidence !== 'string' || !rate.evidence) {
      reject('UNPRICED_NATIVE_MODEL');
    }
    const inputRate = nanos(rate.inputNanosPerToken, 'INVALID_INPUT_PRICE');
    const outputRate = nanos(rate.outputNanosPerToken, 'INVALID_OUTPUT_PRICE');
    // The candidate is intentionally text-only. No cache, tools, media or server-side work.
    if (Object.keys(body).some(key => !['contents', 'systemInstruction', 'generationConfig', 'model'].includes(key))) {
      reject('UNBOUNDED_REQUEST_FEATURE');
    }
    const allContent = [...(Array.isArray(body.contents) ? body.contents : []),
      ...(body.systemInstruction ? [body.systemInstruction] : [])];
    if (!Array.isArray(body.contents) || !body.contents.length ||
        allContent.some(content => !content || typeof content !== 'object' ||
          Object.keys(content).some(key => !['role', 'parts'].includes(key)) ||
          !Array.isArray(content.parts) || !content.parts.length ||
          content.parts.some(part => !part || Object.keys(part).length !== 1 || typeof part.text !== 'string'))) {
      reject('UNBOUNDED_REQUEST_FEATURE');
    }
    const config = body.generationConfig;
    if (!config || Object.keys(config).some(key => !['maxOutputTokens', 'candidateCount'].includes(key)) ||
        (config.candidateCount !== undefined && config.candidateCount !== 1)) {
      reject('UNBOUNDED_GENERATION_CONFIG');
    }
    integer(config.maxOutputTokens, 'MISSING_OUTPUT_LIMIT', true);
    const requestSha256 = crypto.createHash('sha256').update(method + '\n' + url + '\n')
      .update(bodyBytes).digest('hex');
    // This host-owned callback is NOT a client header or an agent-supplied token estimate.
    const bound = await boundForRequest(Object.freeze({model, requestSha256, body: deepFreeze(body)}));
    if (!bound || bound.requestSha256 !== requestSha256 || bound.kind !== 'HOST_VERIFIED_UPPER_BOUND') {
      reject('UNVERIFIED_REQUEST_BOUND');
    }
    const maxInput = integer(bound.maxInputTokens, 'INVALID_INPUT_BOUND', true);
    const maxOutput = integer(bound.maxChargedOutputTokens, 'INVALID_OUTPUT_BOUND', true);
    if (maxOutput < config.maxOutputTokens) reject('OUTPUT_BOUND_TOO_SMALL');
    const reservation = BigInt(maxInput) * inputRate + BigInt(maxOutput) * outputRate;
    const lease = ledger.reserve(reservation); // Synchronous, before forwarding, including concurrent calls.
    try {
      const response = await transport(Object.freeze({method, url, body: Buffer.from(bodyBytes)}));
      const usage = response && response.usageMetadata;
      if (!usage || response.error) reject('MISSING_OR_FAILED_USAGE');
      const actualInput = integer(usage.promptTokenCount, 'INVALID_USAGE');
      const candidateOutput = integer(usage.candidatesTokenCount, 'INVALID_USAGE');
      const thoughtOutput = integer(usage.thoughtsTokenCount ?? 0, 'INVALID_USAGE');
      const actualOutput = integer(candidateOutput + thoughtOutput, 'INVALID_USAGE');
      const total = integer(usage.totalTokenCount, 'INCOMPLETE_USAGE');
      if (total !== integer(actualInput + actualOutput, 'INVALID_USAGE')) reject('INCONSISTENT_USAGE');
      if (actualInput > maxInput || actualOutput > maxOutput ||
          (response.modelVersion !== undefined && response.modelVersion !== model)) {
        reject('USAGE_CONTRACT_BREACH');
      }
      // Charge every input token at full rate; cache discounts cannot understate the reservation.
      ledger.settle(lease, BigInt(actualInput) * inputRate + BigInt(actualOutput) * outputRate);
      return response;
    } catch (error) {
      ledger.halt(); // No retry and no refund on a timeout, missing usage or uncertain charge.
      throw error;
    }
  };
}

module.exports = {GuardError, resolveNativeRequest, validateNativeAdmission, CreditLedger, createBoundedRunner};
