#!/usr/bin/env python3
"""Apply or invert the exact four-source P0D033 S1A candidate into a new tree.

The input tree is read-only. No canonical producer, historical lock, live RC,
permanent progression authority or game publishing operation is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat

HERE = Path(__file__).resolve().parent
SOURCE_LOCK_SHA256 = 'e965a36c2ef10e82e64378af89f7d610a4bad29988800611b18351fca8f52630'
PATCH_SHA256 = 'c0e05f89f3579059180cb4852088bbbba69ee20ba2dc7306f90a462020bff4f5'
PROJECT = 'EGGRUMBLE_REAL69.project.json'
RECEIPT = 'GQ470_S1A_SOURCE_RECEIPT.json'
CHANGED = {
    'ServerScriptService/EGGRUMBLE_SwarmCombat.luau',
    'ServerScriptService/EGGRUMBLE_HeroSilhouetteArt.server.luau',
    'ServerScriptService/EGGRUMBLE_MatchResultService.luau',
    'StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau',
}
BASE_RC = '93a1147561a531610ac1609ebc68cc0ecf546623'


def require(value, reason):
    if not value:
        raise ValueError('RED_GQ470_S1A_' + reason)


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read(path):
    path = Path(path)
    require(not path.is_symlink() and path.is_file() and stat.S_ISREG(path.stat().st_mode),
            'REGULAR_FILE_REQUIRED:' + str(path))
    return path.read_bytes()


def unique_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def safe_root(value):
    path = Path(value).absolute()
    require(not any(p.is_symlink() for p in [path, *path.parents]), 'SYMLINK_ROOT')
    return path.resolve()


def safe_relative(value):
    path = PurePosixPath(value)
    require(isinstance(value, str) and not path.is_absolute() and '..' not in path.parts
            and '\\' not in value and value == path.as_posix(), 'UNSAFE_SOURCE_PATH')
    return value


def source_snapshot(root):
    root = safe_root(root)
    require(root.is_dir(), 'SOURCE_DIRECTORY_REQUIRED')
    result = {}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'SOURCE_SYMLINK')
        if path.is_file():
            relative = safe_relative(path.relative_to(root).as_posix())
            require(path.suffix == '.luau', 'EXTRA_SOURCE_FILE')
            result[relative] = identity(read(path))
        else:
            require(path.is_dir(), 'SPECIAL_SOURCE_FILE')
    return result


def load_contract():
    lock_raw, patch_raw = read(HERE / 'source_lock.json'), read(HERE / 'growth_patch.json')
    require(identity(lock_raw)['sha256'] == SOURCE_LOCK_SHA256, 'SOURCE_LOCK_CHANGED')
    require(identity(patch_raw)['sha256'] == PATCH_SHA256, 'PATCH_CHANGED')
    lock, patch = unique_json(lock_raw), unique_json(patch_raw)
    require(lock['schema'] == 'GQ470_P0D033_S1A_69_SOURCE_LOCK_V1'
            and patch['schema'] == 'GQ470_P0D033_S1A_FOUR_SOURCE_PATCH_V1', 'SCHEMA')
    require(lock['official_input']['head'] == BASE_RC
            and lock['project']['path'] == PROJECT, 'OFFICIAL_BASE')
    before, after = lock['sources_before'], lock['sources_after']
    require(len(before) == len(after) == 69 and set(before) == set(after), 'EXACT69_PATHS')
    require({p for p in before if before[p] != after[p]} == CHANGED
            and set(lock['changed_sources']) == CHANGED, 'EXACT_FOUR_SOURCE_DELTA')
    entries = patch['files']
    require(len(entries) == 4 and {p['path'] for p in entries} == CHANGED, 'FOUR_PATCH_ENTRIES')
    for item in entries:
        relative = safe_relative(item['path'])
        require(item['before'] == before[relative] and item['after'] == after[relative],
                'PATCH_PROFILE_BINDING')
        require(item['hunks'] and len({h['name'] for h in item['hunks']}) == len(item['hunks']),
                'UNIQUE_HUNKS_REQUIRED')
        for hunk in item['hunks']:
            require(isinstance(hunk['old'], str) and isinstance(hunk['new'], str)
                    and hunk['old'] and hunk['new'] and hunk['old'] != hunk['new'],
                    'NONEMPTY_REVERSIBLE_HUNK')
    return lock, patch


def transform(raw, entry, reverse=False):
    expected_before, expected_after = (entry['after'], entry['before']) if reverse else (entry['before'], entry['after'])
    require(identity(raw) == expected_before, 'EXACT_INPUT_SOURCE:' + entry['path'])
    result = raw
    hunks = list(reversed(entry['hunks'])) if reverse else entry['hunks']
    for hunk in hunks:
        old, new = (hunk['new'], hunk['old']) if reverse else (hunk['old'], hunk['new'])
        old, new = old.encode('utf-8'), new.encode('utf-8')
        require(result.count(old) == 1, 'HUNK_NOT_UNIQUE:' + hunk['name'])
        result = result.replace(old, new, 1)
    require(identity(result) == expected_after, 'EXACT_OUTPUT_SOURCE:' + entry['path'])
    return result


def apply(source, output, reverse=False):
    lock, patch = load_contract()
    source, output = safe_root(source), safe_root(output)
    require(source != output and not source.is_relative_to(output)
            and not output.is_relative_to(source), 'OVERLAPPING_INPUT_OUTPUT')
    require(not output.exists(), 'OUTPUT_MUST_BE_NEW')
    expected = lock['sources_after'] if reverse else lock['sources_before']
    wanted = lock['sources_before'] if reverse else lock['sources_after']
    before = source_snapshot(source / 'sources')
    require(before == expected, 'ENTIRE69_INPUT_PROFILE')
    project = read(source / PROJECT)
    require(identity(project) == {k: lock['project'][k] for k in ('bytes', 'sha256')}, 'PROJECT_CHANGED')
    selected = {path: read(source / 'sources' / path) for path in before}
    transformed = dict(selected)
    for entry in patch['files']:
        path = entry['path']
        transformed[path] = transform(selected[path], entry, reverse)
        require(transform(transformed[path], entry, not reverse) == selected[path], 'INVERSE_NOT_EXACT')
    require({p: identity(raw) for p, raw in transformed.items()} == wanted, 'ENTIRE69_OUTPUT_PROFILE')
    # Validate everything before the first write. Never patch an input in place.
    output.mkdir(parents=True, exist_ok=False)
    for relative, raw in transformed.items():
        target = output / 'sources' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (output / PROJECT).write_bytes(project)
    require(source_snapshot(source / 'sources') == before and read(source / PROJECT) == project,
            'INPUT_MUTATION')
    require(source_snapshot(output / 'sources') == wanted, 'WRITTEN_PROFILE_MISMATCH')
    report = {
        'schema': 'GQ470_P0D033_S1A_SOURCE_TRANSFORM_V1',
        'status': 'PASS_EXACT_SOURCE_TRANSFORM_ONLY',
        'direction': 'OFF_EXACT_H93' if reverse else 'ON_S1A_CANDIDATE',
        'official_input': lock['official_input'],
        'scope_claim': lock['scope_claim'],
        'source_count': 69, 'changed_count': 4, 'unchanged_count': 65,
        'before_profile': before, 'after_profile': wanted,
        'project': lock['project'], 'input_unchanged': True,
        'patch': identity(read(HERE / 'growth_patch.json')),
        'source_lock': identity(read(HERE / 'source_lock.json')),
        'applier': identity(read(Path(__file__))),
        'native': 'NOT_RUN_BY_APPLIER', 'rojo': 'NOT_RUN_BY_APPLIER',
        'formal_rc_adoption': False, 'runtime_unified': False,
        'persistent_growth_wired': False, 'full_S1_MVP_complete': False,
        'studio': 'NOT_TESTED', 'android': 'NOT_TESTED', 'art': 'ART_NO_GO', 'fun': 'NOT_TESTED',
    }
    (output / RECEIPT).write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--reverse', action='store_true')
    args = parser.parse_args()
    report = apply(args.input, args.out, args.reverse)
    print(report['direction'] + ': four exact sources, 65 unchanged, project preserved; no engine acceptance')


if __name__ == '__main__':
    main()
