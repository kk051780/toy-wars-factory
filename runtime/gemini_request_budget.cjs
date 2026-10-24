'use strict';
// Diagnostic math only. This cannot issue an admission lease or certify an input count.
const {GuardError} = require('./gemini_budget_guard.cjs');
const {loadOfflineProfile} = require('./gemini_offline_gateway.cjs');

function inspectRequestBudget(snapshot, outputTokens, remainingNanos = 10000000000n, now = new Date()) {
  const profile = loadOfflineProfile(snapshot, now);
  if (!Number.isSafeInteger(outputTokens) || outputTokens <= 0 || outputTokens > snapshot.output_token_limit ||
      typeof remainingNanos !== 'bigint' || remainingNanos < 0n || remainingNanos > 10000000000n) {
    throw new GuardError('INVALID_REQUEST_BUDGET');
  }
  const rate = profile.catalog.get(snapshot.model);
  const outputReservation = BigInt(outputTokens) * rate.outputNanosPerToken;
  const maximumInputToFit = remainingNanos >= outputReservation ?
    (remainingNanos - outputReservation) / rate.inputNanosPerToken : 0n;
  const provenInput = BigInt(snapshot.input_token_limit);
  const reserved = provenInput * rate.inputNanosPerToken + outputReservation;
  return {
    status: reserved > remainingNanos ? 'BLOCKED_NO_VERIFIED_SMALL_INPUT_BOUND' : 'MODEL_CEILING_FITS',
    model: snapshot.model, requestedOutputTokens: outputTokens,
    chargedOutputBoundIncludesThinking: true,
    currentProvenInputBound: String(provenInput),
    requiredInputCeilingToFit: String(maximumInputToFit > provenInput ? provenInput : maximumInputToFit),
    reservationNanocredits: String(reserved), remainingNanocredits: String(remainingNanos),
    requestSpecificInputProofAvailable: false, admissionGranted: false,
    note: 'The input threshold is a requirement for a future proof, not a measured or certified input count.'
  };
}
module.exports = {inspectRequestBudget};
