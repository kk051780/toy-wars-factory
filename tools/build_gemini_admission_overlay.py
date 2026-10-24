#!/usr/bin/env python3
"""Build a hash-checked, offline AWF overlay. Never installs or deploys it."""
import argparse
import hashlib
import json
from pathlib import Path

PIN = 'f50f31b6751c03221d7fa9aae2e3f87a0327d1d4'
ROOT = Path(__file__).resolve().parents[1]


def build(upstream, destination):
    if destination.resolve().is_relative_to(upstream.resolve()):
        raise ValueError('Output must be outside the pinned upstream checkout')
    source = (upstream / 'containers/api-proxy/proxy-guards.js').read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(source)).encode() + b'\0' + source).hexdigest()
    if actual != PIN:
        raise ValueError('Upstream proxy blob differs from the reviewed v0.28.70 pin')
    text = source.decode('utf-8')
    marker = "  const model = checkModelMultiplier ? extractModelFromBody(body) : null;"
    if text.count(marker) != 1 or text.count('\n  checkUnknownModelRejection,\n') != 1:
        raise ValueError('Unexpected upstream hook shape')
    text = text.replace("'use strict';", "'use strict';\nconst { validateNativeAdmission } = require('./twf-gemini-budget-guard');", 1)
    text = text.replace('  checkUnknownModelRejection,\n', '  checkUnknownModelRejection,\n  isModelPriceable,\n', 1)
    hook = '''  let model = checkModelMultiplier ? extractModelFromBody(body) : null;
  if (provider === 'gemini' && checkModelMultiplier) {
    const admission = validateNativeAdmission(req, body, isModelPriceable);
    if (!admission.ok) {
      sendGuardBlockedResponse(admission, {
        req, res, provider, requestId, startTime, span, body, inboundBytes,
        statusCode: 400, eventName: 'native_gemini_admission_rejected',
        buildError: block => ({error: block.error}),
        buildLogFields: block => ({reason: block.error.type}),
      });
      return true;
    }
    model = admission.model;
  }'''
    text = text.replace(marker, hook, 1)
    helper = (ROOT / 'runtime/gemini_budget_guard.cjs').read_bytes()
    files = {'proxy-guards.js': text.encode(), 'twf-gemini-budget-guard.js': helper}
    manifest = {
        'status': 'OFFLINE_CANDIDATE_NOT_DEPLOYED',
        'upstream': 'github/gh-aw-firewall@32c12e0099763dad77acef6c655cb12e58fe36e1',
        'original_proxy_git_blob': PIN,
        'files_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
        'provider_calls': 0,
        'limits': ['Overlay hooks native admission only.',
                   'Bounded runner requires a trusted token-bound adapter and approved price profile.',
                   'No live provider spending cap or billing verification is claimed.'],
    }
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (destination / name).write_bytes(data)
    (destination / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.upstream, args.output), indent=2))
