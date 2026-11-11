#!/usr/bin/env python3
"""Read-only S1 official RC -> candidate manifest intake gate. Does not copy files.

Usage: python tools/rc_intake_preflight.py --rc original.json --candidate candidate.json [--expected docs/OBSERVED_DIFF.json]
"""
from __future__ import annotations
import argparse
import json
import pathlib
import re
import sys

ROOT_KEYS = frozenset({'format','game_id','work_id','packet_id','public_source_allowed','files'})
HEX64 = re.compile(r'^[a-f0-9]{64}$')
PATH = re.compile(r'^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$')


class InvalidManifest(ValueError):
    pass


def validate(m: object, *, original: bool = False) -> dict[str, dict]:
    if type(m) is not dict:
        raise InvalidManifest('root_not_dict')
    keys = set(m)
    allowed = ROOT_KEYS | ({'status'} if original else set())
    if not ROOT_KEYS.issubset(keys) or not keys.issubset(allowed):
        raise InvalidManifest('invalid_manifest_top_keys')
    if m['format'] != 'P0D_PUBLIC_SOURCE_V1' or m['game_id'] != 'TRAP_RAIDERS' or m['work_id'] != 'p0d-siege-v19':
        raise InvalidManifest('wrong_source_contract')
    if m['public_source_allowed'] is not True or not isinstance(m['packet_id'], str) or not m['packet_id']:
        raise InvalidManifest('wrong_source_authorization')
    if type(m['files']) is not list or not m['files']:
        raise InvalidManifest('missing_source_entries')
    parsed: dict[str, dict] = {}
    for f in m['files']:
        if type(f) is not dict or set(f) != {'path','sha256','size'}:
            raise InvalidManifest('invalid_file_record')
        path, digest, size = f['path'], f['sha256'], f['size']
        if type(path) is not str or not PATH.fullmatch(path) or any(x in ('.','..') for x in path.split('/')):
            raise InvalidManifest('unsafe_path')
        if type(digest) is not str or not HEX64.fullmatch(digest):
            raise InvalidManifest('bad_sha256')
        if type(size) is not int or not (0 <= size <= 50_000_000):
            raise InvalidManifest('bad_size')
        if path in parsed:
            raise InvalidManifest('duplicate_path')
        parsed[path] = {'sha256': digest, 'size': size}
    return parsed


def compare(rc: object, candidate: object) -> dict:
    old = validate(rc, original=True)
    new = validate(candidate)
    removed = sorted(set(old) - set(new))
    if removed:
        raise InvalidManifest('unexpected_removed_files:' + ','.join(removed))
    unchanged = sorted(p for p in new if p in old and old[p] == new[p])
    changed = sorted(p for p in new if p in old and old[p] != new[p])
    added = sorted(p for p in new if p not in old)
    return {
        'schema': 'P0D_S1_RC_INTAKE_DIFF_V1',
        'rc_files': len(old), 'candidate_files': len(new),
        'unchanged': unchanged, 'changed': changed, 'added': added,
        'removed': removed,
        'counts': {'unchanged': len(unchanged), 'changed': len(changed), 'added': len(added), 'removed': 0},
        'legacy_rc_manifest_extra_status': 'status' in rc,
        'candidate_manifest_six_keys': set(candidate) == ROOT_KEYS,
        'game_release_pct': 'UNSCORED__ONLY_ISSUE_220_CHAT_INTEGRATOR',
        'official_rc_files_modified': 0,
        'note': 'Only compares source metadata. Does not execute, hash retrieved bytes, overwrite RC, or approve release.'
    }


def validate_observed(actual: dict, expected: dict) -> None:
    for key in ('rc_files','candidate_files','counts','unchanged','changed','added','removed','legacy_rc_manifest_extra_status','candidate_manifest_six_keys'):
        if actual.get(key) != expected.get(key):
            raise InvalidManifest('EXPECTED_SOURCE_DRIFT:' + key)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rc', type=pathlib.Path, required=True)
    parser.add_argument('--candidate', type=pathlib.Path, required=True)
    parser.add_argument('--expected', type=pathlib.Path)
    args = parser.parse_args()
    try:
        old = json.loads(args.rc.read_text(encoding='utf-8'))
        new = json.loads(args.candidate.read_text(encoding='utf-8'))
        report = compare(old, new)
        if args.expected:
            validate_observed(report, json.loads(args.expected.read_text(encoding='utf-8')))
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print('P0D_S1_RC_INTAKE_PREFLIGHT_FAIL:', str(e), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    print('P0D_S1_RC_INTAKE_METADATA_PASS__NOT_INTEGRATED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
