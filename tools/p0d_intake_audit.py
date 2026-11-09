#!/usr/bin/env python3
"""Read-only PUBLIC ciphertext intake checker for P0-D.

Does not decrypt, install, extract, merge, run Roblox, write to a repository,
or infer any Windows/Studio validation from GitHub access.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.request import Request, urlopen

REPO = 'kk051780/toy-wars-factory'
RAW_HOST = 'https://raw.githubusercontent.com/'
SCHEMA = 'P0D_READONLY_INTAKE_V1'
SHA1 = re.compile(r'[a-f0-9]{40}\Z')
SHA256 = re.compile(r'[a-f0-9]{64}\Z')
PACKET_ID = re.compile(r'[A-Za-z0-9_.-]{1,96}\Z')
MAX_REGISTRY = 200_000
MAX_BLOB = 500_000
MIN_ENVELOPE = 200


class AuditError(ValueError):
    pass


def _strict_json(raw: bytes | str):
    def reject_duplicates(items):
        out = {}
        for key, value in items:
            if key in out:
                raise AuditError('DUPLICATE_JSON_KEY')
            out[key] = value
        return out
    try:
        return json.loads(raw, object_pairs_hook=reject_duplicates)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError('INVALID_JSON') from exc


def _sha(value, regex, label):
    if not isinstance(value, str) or not regex.fullmatch(value):
        raise AuditError(f'BAD_{label}')


def _safe_path(value):
    if not isinstance(value, str) or not value.startswith('handoffs/') or len(value) > 180:
        raise AuditError('UNSAFE_ARTIFACT_PATH')
    # Reject URLs, path traversal and percent-encoding that could change meaning.
    if '\\' in value or ':' in value or '%' in value or '?' in value or '#' in value:
        raise AuditError('UNSAFE_ARTIFACT_PATH')
    parts = value.split('/')
    if any(not part or part in ('.', '..') or not re.fullmatch(r'[A-Za-z0-9_.-]+', part) for part in parts):
        raise AuditError('UNSAFE_ARTIFACT_PATH')
    if str(PurePosixPath(value)) != value:
        raise AuditError('UNSAFE_ARTIFACT_PATH')


def _assert_no_secrets(tree):
    forbidden = {'private_key', 'private_key_b64', 'secret', 'password', 'api_token', 'auth_token', 'access_token'}
    if isinstance(tree, dict):
        for key, value in tree.items():
            if key.lower() in forbidden:
                raise AuditError('SECRET_FIELD_IN_PUBLIC_REGISTRY')
            _assert_no_secrets(value)
    elif isinstance(tree, list):
        for x in tree:
            _assert_no_secrets(x)


def validate_registry(doc):
    if not isinstance(doc, dict) or doc.get('schema') != SCHEMA:
        raise AuditError('BAD_SCHEMA')
    _assert_no_secrets(doc)
    if (doc.get('repo') != REPO or doc.get('game_id') != 'TRAP_RAIDERS'
            or doc.get('work_id') != 'p0d-siege-v19'):
        raise AuditError('BAD_PROJECT_IDENTITY')
    if doc.get('pc_status') != 'PARTIAL_NOT_READY':
        raise AuditError('UNSUPPORTED_PC_STATUS_WITHOUT_EVIDENCE')
    base = doc.get('baseline_feature_ids')
    if base != [f'D{i:02}' for i in range(1, 18)]:
        raise AuditError('BAD_FEATURE_BASELINE')
    pc = doc.get('pc_partial_feature_ids')
    if pc != [f'D{i:02}' for i in range(1, 6)]:
        raise AuditError('BAD_PARTIAL_PC_FEATURES')
    _sha(doc.get('pc_reference_sha256'), SHA256, 'PC_REFERENCE_SHA')
    packets = doc.get('sealed_packets')
    if not isinstance(packets, list) or len(packets) > 100 or not packets:
        raise AuditError('NO_VALID_PACKETS')
    seen = set()
    seen_artifacts = set()
    features = set()
    for pack in packets:
        if not isinstance(pack, dict):
            raise AuditError('BAD_PACKET')
        ident = pack.get('packet_id')
        if not isinstance(ident, str) or not PACKET_ID.fullmatch(ident) or ident in seen:
            raise AuditError('DUPLICATE_OR_BAD_PACKET_ID')
        seen.add(ident)
        fs = pack.get('feature_ids')
        if not isinstance(fs, list) or not fs or len(fs) != len(set(fs)) or not set(fs).issubset(set(base)):
            raise AuditError('BAD_PACKET_FEATURE_IDS')
        features.update(fs)
        commit = pack.get('commit')
        _sha(commit, SHA1, 'COMMIT')
        for role in ('envelope', 'readme'):
            path = pack.get(role + '_path')
            blob = pack.get(role + '_blob_sha1')
            _safe_path(path)
            _sha(blob, SHA1, role.upper() + '_BLOB_SHA1')
            if (commit, path) in seen_artifacts:
                raise AuditError('SAME_COMMIT_PATH_REUSED')
            seen_artifacts.add((commit, path))
        if not pack['envelope_path'].endswith('.json') or not pack['readme_path'].endswith('.md'):
            raise AuditError('WRONG_FILE_TYPES')
        _sha(pack.get('zip_sha256'), SHA256, 'ZIP_SHA')
        if pack.get('transport') != 'AES256_GCM_PUBLIC_CIPHERTEXT':
            raise AuditError('BAD_TRANSPORT')
        if pack.get('windows_restore') != 'NOT_TESTED' or pack.get('studio_qa') != 'NOT_TESTED':
            raise AuditError('PC_QA_CANNOT_BE_AUTO_CLAIMED')
        deps = pack.get('depends_on_packets')
        if not isinstance(deps, list) or len(deps) != len(set(deps)) or not all(isinstance(d, str) for d in deps):
            raise AuditError('BAD_DEPENDENCIES')
        if not isinstance(pack.get('pc_gate'), str) or not pack['pc_gate'].startswith('AFTER_'):
            raise AuditError('MISSING_PC_GATE')
    for pack in packets:
        if pack['packet_id'] in pack['depends_on_packets'] or any(d not in seen for d in pack['depends_on_packets']):
            raise AuditError('MISSING_OR_SELF_DEPENDENCY')
    # Cycle detection: any cycle makes intake sequence ambiguous.
    graph = {p['packet_id']: p['depends_on_packets'] for p in packets}
    visited, active = set(), set()
    def visit(p):
        if p in active:
            raise AuditError('DEPENDENCY_CYCLE')
        if p in visited:
            return
        active.add(p)
        for d in graph[p]:
            visit(d)
        active.remove(p)
        visited.add(p)
    for key in graph:
        visit(key)
    if not (set(pc) | features).issubset(set(base)):
        raise AuditError('FEATURE_OUTSIDE_BASELINE')
    return {'packets': len(packets), 'pc_partial_features': len(set(pc)),
            'github_reference_features': len(features),
            'candidate_features': len(set(pc) | features),
            'baseline_features': len(base),
            'pc_restored_verified': 0, 'studio_qa_from_reference_pass': 0}


def _b64(value, label):
    if isinstance(value, list):
        if not value or not all(isinstance(x, str) for x in value):
            raise AuditError('BAD_'+label)
        value = ''.join(value)
    if not isinstance(value, str) or len(value) > MAX_BLOB * 2:
        raise AuditError('BAD_'+label)
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise AuditError('BAD_'+label) from exc


def git_blob_sha1(blob: bytes) -> str:
    return hashlib.sha1(b'blob '+str(len(blob)).encode('ascii')+b'\x00'+blob).hexdigest()


def verify_envelope_bytes(data: bytes, pack: dict, *, game_id='TRAP_RAIDERS', work_id='p0d-siege-v19'):
    if not MIN_ENVELOPE <= len(data) <= MAX_BLOB:
        raise AuditError('ENVELOPE_SIZE_REJECTED')
    if git_blob_sha1(data) != pack['envelope_blob_sha1']:
        raise AuditError('ENVELOPE_BLOB_MISMATCH')
    doc = _strict_json(data)
    if not isinstance(doc, dict):
        raise AuditError('INVALID_ENVELOPE')
    if (doc.get('format') != 'P0D_AES256_GCM_HANDOFF_V1'
            or doc.get('packet_id') != pack['packet_id']
            or doc.get('game_id') != game_id
            or doc.get('work_id') != work_id
            or doc.get('zip_sha256') != pack['zip_sha256']
            or doc.get('private_key_not_included') is not True):
        raise AuditError('ENVELOPE_IDENTITY_MISMATCH')
    nonce = _b64(doc.get('nonce_b64'), 'NONCE')
    aad = _b64(doc.get('aad_b64'), 'AAD')
    ciphertext = _b64(doc.get('ciphertext_b64'), 'CIPHERTEXT')
    if len(nonce) != 12 or len(ciphertext) < 16:
        raise AuditError('BAD_ENVELOPE_CRYPTO_SHAPE')
    expected_aad = f'{game_id}|{work_id}|{pack["packet_id"]}|zip_sha256={pack["zip_sha256"]}'.encode()
    if aad != expected_aad or hashlib.sha256(ciphertext).hexdigest() != doc.get('ciphertext_sha256'):
        raise AuditError('ENVELOPE_CIPHER_INTEGRITY_FAIL')
    return True


def verify_readme_bytes(data: bytes, pack: dict):
    if not data or len(data) > MAX_BLOB or git_blob_sha1(data) != pack['readme_blob_sha1']:
        raise AuditError('README_BLOB_MISMATCH')
    return True


def fetch_pinned(commit: str, path: str) -> bytes:
    # Pinned SHA and strict path have been validated before use.
    url = RAW_HOST + REPO + '/' + commit + '/' + path
    request = Request(url, headers={'User-Agent':'P0D-readonly-intake-audit/1.0', 'Accept':'text/plain'})
    with urlopen(request, timeout=15) as response:
        data = response.read(MAX_BLOB + 1)
    if len(data) > MAX_BLOB:
        raise AuditError('REMOTE_BLOB_TOO_LARGE')
    return data


def audit(doc: dict, fetcher=fetch_pinned):
    summary = validate_registry(doc)
    checks = []
    for pack in doc['sealed_packets']:
        result = {'packet_id': pack['packet_id'], 'commit': pack['commit'],
                  'stage': 'GITHUB_CIPHERTEXT_ONLY', 'pc_restored': 'NOT_TESTED',
                  'studio_qa': 'NOT_TESTED'}
        try:
            enc = fetcher(pack['commit'], pack['envelope_path'])
            note = fetcher(pack['commit'], pack['readme_path'])
            verify_envelope_bytes(enc, pack, game_id=doc['game_id'], work_id=doc['work_id'])
            verify_readme_bytes(note, pack)
            result['readback'] = 'PASS'
        except Exception as exc:
            result['readback'] = 'BLOCKED'
            result['reason'] = type(exc).__name__
        checks.append(result)
    summary['remote_file_pairs_checked'] = len(checks)
    summary['remote_file_pairs_pass'] = sum(c['readback']=='PASS' for c in checks)
    summary['readback_status'] = 'PASS' if summary['remote_file_pairs_pass'] == len(checks) else 'BLOCKED'
    return summary, checks


def build_report(doc, *, verified=None):
    c = validate_registry(doc)
    result = dict(schema='P0D_INTAKE_REPORT_V1', source='GITHUB_PUBLIC_METADATA_ONLY',
                  game_id=doc['game_id'], work_id=doc['work_id'],
                  summary=c, pc_status=doc['pc_status'],
                  primary_blocker='V37_SAVED_PLACE_FINAL_MULTICLIENT_QA_NOT_ATTESTED',
                  next_owner_codex_gate='VERIFY_PC_SHA_THEN_V37_FINAL_QA_THEN_V39_ONE_PACKET',
                  safe_resume='OWNER_DIRECT_TO_PC_ONLY',
                  warning='REFERENCE_PACKET != WINDOWS_RESTORED != STUDIO_INTEGRATED != STUDIO_QA_PASS',
                  queue=[{'packet_id':p['packet_id'], 'feature_ids':p['feature_ids'], 'commit':p['commit'],
                          'zip_sha256':p['zip_sha256'], 'gate':p['pc_gate'],
                          'dependencies':p['depends_on_packets'],
                          'status':'DEPENDENCY_HOLD_NOT_PC_READY',
                          'url':'https://github.com/'+REPO+'/blob/'+p['commit']+'/'+p['envelope_path']}
                         for p in doc['sealed_packets']])
    if verified is not None:
        result['remote_verification']={'summary':verified[0], 'files':verified[1]}
    else:
        result['remote_verification']={'status':'NOT_RUN_THIS_COMMAND',
                                      'note':'Registry snapshot has previously read back files; this run did not contact GitHub'}
    return result


def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--registry',type=Path,required=True)
    a.add_argument('--verify-remote',action='store_true',help='read 2 pinned PUBLIC GitHub files per packet; never decrypt')
    a.add_argument('--output',type=Path,help='optional explicit report JSON path; fails if exists')
    args=a.parse_args(argv)
    try:
        if args.registry.is_symlink() or args.registry.stat().st_size > MAX_REGISTRY:
            raise AuditError('BAD_REGISTRY_FILE')
        doc=_strict_json(args.registry.read_bytes())
        validate_registry(doc)
        verified=audit(doc) if args.verify_remote else None
        report=build_report(doc,verified=verified)
        blob=(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
        if args.output:
            # Exclusive creation: never overwrite a report or protected file.
            with args.output.open('xb') as file:
                file.write(blob)
        else:
            sys.stdout.buffer.write(blob)
        return 2 if verified and verified[0]['readback_status'] != 'PASS' else 0
    except (AuditError, OSError, ValueError, TypeError) as exc:
        print('AUDIT_BLOCKED: '+type(exc).__name__+' ('+str(exc).split(':')[0][:100]+')',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
