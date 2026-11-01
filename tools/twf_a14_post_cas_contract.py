"""Offline compatibility witness between protected PR158, PR175 and POST candidate.

Pure JSON/value checks: NO HTTP, GitHub I/O, provider authentication, credentials,
POST approval or engine proof. All inputs could be forged by the caller. A trusted
host must independently authenticate the original GitHub commit and Roblox target.
"""
from __future__ import annotations
import hashlib
import json
import re

from twf_roblox_task_post_once import FixedRequest, Target, prepare

_SHA1 = re.compile(r'[0-9a-f]{40}\Z')
_SHA256 = re.compile(r'[0-9a-f]{64}\Z')
_POS = re.compile(r'[1-9][0-9]{0,18}\Z')
REPO = 'kk051780/toy-wars-factory'
EXPECTED_MAIN = 'e5deff4d5681bca4823a3da0f848e01bc089ae6e'
PINNED_PRODUCER_RUN = 41137070161
PINNED_ARTIFACT_ID = 13015999142
PINNED_ZIP_SHA256 = '2f662dad3e0fd81d71aaa52f34fcf1be56406cf6aecc5637b30f6de8bdac3b7b'
PINNED_XML_SHA256 = '1c9bdc3dc478fe72e51870e478aa15392c47875618b86262aa7dd605e4026b33'
PINNED_XML_BYTES = 54753
INTENT_KEYS = frozenset(('repository', 'source_main_sha', 'artifact_zip_sha256',
                         'rbxlx_sha256', 'luau_sha256', 'universe_id', 'place_id',
                         'version_id', 'intent_type'))
RECORD_KEYS = frozenset(('fingerprint','resource','source_main_sha', 'owner_id',
                         'epoch','claim_ref','reserved_at','phase'))
READBACK_KEYS = frozenset(('status','record_fingerprint','source_ref',
                           'observed_ref','post_authorized',
                           'github_provider_authenticated','roblox_engine_verified',
                           'replay_authorized','merge_authorized'))

class AlignmentHold(ValueError):
    """A fixed, redacted diagnostic token; never propagate raw inputs."""

def must(condition: bool, message: str) -> None:
    if not condition:
        raise AlignmentHold(message)

def sha1(value):
    return type(value) is str and _SHA1.fullmatch(value) is not None

def sha256(value):
    return type(value) is str and _SHA256.fullmatch(value) is not None

def positive(value):
    return type(value) is int and 1 <= value <= (2**63 - 1)

def digest_intent(intent: dict) -> str:
    """Byte-compatible with draft PR158 request_id() canonical fingerprint."""
    must(type(intent) is dict and frozenset(intent) == INTENT_KEYS, 'INTENT_SCHEMA_MISMATCH')
    must(intent['repository'] == REPO and intent['intent_type'] == 'HEADLESS_SERVER_SMOKE_V1',
         'FOREIGN_INTENT')
    must(sha1(intent['source_main_sha']) and all(sha256(intent[k]) for k in
        ('artifact_zip_sha256','rbxlx_sha256','luau_sha256')),
         'INVALID_INTENT_DIGEST')
    must(all(positive(intent[k]) for k in ('universe_id','place_id','version_id')),
         'INVALID_INTENT_TARGET')
    return hashlib.sha256(json.dumps(intent, sort_keys=True,
            separators=(',', ':'),ensure_ascii=True).encode('ascii')).hexdigest()

def verify_alignment(*, plan: dict, intent: dict, proposal: dict,
                     readback: dict, fixed_request: FixedRequest,
                     target: Target, smoke_script: bytes) -> dict:
    """Only static compatibility; even PASS cannot authorize a Roblox POST.

    No Python callbacks, secret, raw response, network or CAS operation accepted.
    A test-only forged CAS receipt can pass; therefore the returned flags cannot
    authorize dispatch and any external host MUST verify provider origin itself.
    """
    must(type(plan) is dict and plan.get('status') == 'PRIVATE_OPEN_CLOUD_PLAN_NOT_EXECUTED'
         and type(plan.get('request')) is dict, 'PLAN_NOT_REVIEWED')
    must(type(target) is Target and type(fixed_request) is FixedRequest,
         'BAD_LOCAL_POST_REQUEST')
    try:
        canonical = prepare(target, smoke_script)
    except Exception:
        raise AlignmentHold('BAD_LOCAL_POST_REQUEST') from None
    must(fixed_request == canonical, 'MUTATED_POST_REQUEST')
    p = plan['request']
    must(plan.get('repository') == REPO and plan.get('source_main_sha') == EXPECTED_MAIN,
         'STALE_SOURCE_MAIN')
    must(type(plan.get('artifact_id')) is int and plan['artifact_id'] > 0 and
         type(plan.get('producer_run_id')) is int and plan['producer_run_id'] > 0 and
         sha256(plan.get('zip_sha256')) and sha256(plan.get('xml_sha256')) and
         type(plan.get('xml_bytes')) is int and 0 < plan['xml_bytes'] <= 10_000_000,
         'UNPINNED_BUILD_ARTIFACT')
    must(plan['artifact_id'] == PINNED_ARTIFACT_ID and
         plan['producer_run_id'] == PINNED_PRODUCER_RUN and
         plan['zip_sha256'] == PINNED_ZIP_SHA256 and
         plan['xml_sha256'] == PINNED_XML_SHA256 and
         plan['xml_bytes'] == PINNED_XML_BYTES,
         'ARTIFACT_NOT_PR175_PINNED')
    must(plan.get('script_sha256') == fixed_request.script_sha256,
         'PLAN_SCRIPT_MISMATCH')
    must(p.get('method') == 'POST' and p.get('api_host') == 'https://apis.roblox.com' and
         p.get('path') == '/cloud/v2/' + target.create_path() and
         p.get('body_sha256') == fixed_request.body_sha256 and
         p.get('explicit_version_id') == int(target.saved_version_id) and
         p.get('universe_id') == int(target.universe_id) and
         p.get('place_id') == int(target.place_id) and
         p.get('timeout') == '30s' and p.get('content_type') == 'application/json' and
         p.get('body_contains_exact_reviewed_script') is True and
         p.get('credentials_embedded') is False and
         p.get('body_embedded_in_report') is False,
         'POST_PLAN_REQUEST_MISMATCH')
    fp = digest_intent(intent)
    must(intent['source_main_sha'] == EXPECTED_MAIN and
         intent['artifact_zip_sha256'] == plan['zip_sha256'] and
         intent['rbxlx_sha256'] == plan['xml_sha256'] and
         intent['luau_sha256'] == fixed_request.script_sha256,
         'BUILD_OR_SCRIPT_INTENT_MISMATCH')
    must((intent['universe_id'],intent['place_id'],intent['version_id']) ==
         (int(target.universe_id),int(target.place_id),int(target.saved_version_id)),
         'INTENT_TARGET_MISMATCH')
    must(type(proposal) is dict and proposal.get('status') == 'CANDIDATE_ONLY_NO_WRITE'
         and type(proposal.get('next_state')) is dict and
         type(proposal.get('record')) is dict and sha1(proposal.get('expected_sha')),
         'RESERVATION_PROPOSAL_MISSING')
    must(all(proposal.get(k) is False for k in
             ('post_authorized','provider_attested','roblox_engine_verified',
              'main_merge_authorized')), 'PROPOSAL_FALSE_AUTHORITY_REQUIRED')
    rec=proposal['record']
    must(frozenset(rec) == RECORD_KEYS and rec.get('fingerprint') == fp and
         rec.get('resource') == '/'.join((target.universe_id, target.place_id,
                                         target.saved_version_id)) and
         rec.get('source_main_sha') == EXPECTED_MAIN and
         rec.get('phase') == 'POST_CONSUMED_NEVER_AUTO_RETRY' and
         sha1(rec.get('claim_ref')) and rec['claim_ref'] == proposal['expected_sha'] and
         type(rec.get('epoch')) is int and rec['epoch'] > 0 and
         type(rec.get('owner_id')) is str and bool(rec['owner_id']) and
         type(rec.get('reserved_at')) is str and bool(rec['reserved_at']),
         'RESERVATION_RECORD_MISMATCH')
    next_state=proposal['next_state']
    records=next_state.get('cloud_execution_intents_v1')
    must(type(records) is list and bool(records) and records[-1] == rec and
         type(next_state.get('epoch')) is int and next_state['epoch'] == rec['epoch'] and
         type(next_state.get('holder')) is dict and
         next_state['holder'].get('owner_id') == rec['owner_id'] and
         next_state['holder'].get('epoch') == rec['epoch'] and
         next_state['holder'].get('kind') == 'CONTROLLER' and
         next_state['holder'].get('origin') == 'controller' and
         next_state['holder'].get('task_id') is None and
         type(next_state['holder'].get('work_branch')) is str and
         next_state['holder']['work_branch'].startswith('controller/roblox-cloud-') and
         next_state['holder'].get('base_main_sha') == EXPECTED_MAIN,
         'RESERVATION_LEDGER_MISMATCH')
    must(type(readback) is dict and frozenset(readback) == READBACK_KEYS and
         readback.get('status') == 'EXACT_PARENT_CAS_READBACK_STRUCTURAL_ONLY' and
         readback.get('record_fingerprint') == fp and
         readback.get('source_ref') == rec['claim_ref'] and
         sha1(readback.get('observed_ref')) and
         readback['observed_ref'] != rec['claim_ref'] and
         all(readback.get(k) is False for k in
             ('post_authorized','github_provider_authenticated','roblox_engine_verified',
              'replay_authorized','merge_authorized')),
         'READBACK_STRUCTURAL_PROOF_MISMATCH')
    return {
        'status': 'UNTRUSTED_PR158_PR175_POST_CONTRACTS_ALIGN',
        'resource_key_sha256': hashlib.sha256(rec['resource'].encode('ascii')).hexdigest(),
        'intent_fingerprint': fp,
        'post_body_sha256': fixed_request.body_sha256,
        'script_sha256': fixed_request.script_sha256,
        'plan_artifact_source_sha256': plan['zip_sha256'],
        'plan_xml_sha256': plan['xml_sha256'],
        'provider_authenticated': False,
        'github_cas_provider_authenticated': False,
        'roblox_provider_authenticated': False,
        'target_private_verified': False,
        'saved_version_authenticated': False,
        'global_intent_authentic': False,
        'post_authorized': False,
        'may_post': False,
        'may_retry': False,
        'may_publish': False,
        'may_merge': False,
        'may_spend': False,
        'engine_verified': False,
        'network_calls': 0,
    }
