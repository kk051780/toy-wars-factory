#!/usr/bin/env python3
"""Compile/run one shared full-source shop suite for original and local proposal.

No repository, artifact or input source is modified. This is standalone Native
Luau evidence, NOT_STUDIO and not official CI, adoption or commerce acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

PINS = {
    'ReplicatedStorage/GQ805Shop/EGGRUMBLE_LobbyShopCatalog.luau':
        (4506, 'c9418ebec21b6ca1550a2f3aa1970631127087d1cc0fbd4e866d71b7644dc792'),
    'ReplicatedStorage/GQ805Shop/EGGRUMBLE_LobbyShopView.luau':
        (6116, '6beac564c1875ed77786fbd094ac1aea18dbee449dfc507acac40b32dde123fe'),
    'StarterPlayer/StarterPlayerScripts/GQ805_ShopKioskClient.client.luau':
        (2170, 'b381bf0e4db6c5382f3621524eb3bc1e20f63b2977f3809c79adab85774b176d'),
}
MARKERS = ('--@@FULL_SOURCE_CATALOG@@', '--@@FULL_SOURCE_VIEW@@', '--@@FULL_SOURCE_KIOSK@@')
OFFICIAL_SOURCE_BASE = '93a1147561a531610ac1609ebc68cc0ecf546623'
CASE_COUNT = 38
READONLY_CONTROLS = 38
TERMINAL_LINE = b"if failed>0 then error('NATIVE_SHOP_LIFECYCLE_FAILURES='..failed) end"


def identity(raw: bytes) -> dict:
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read_regular(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'not a regular input file: {path}')
    return path.read_bytes()


def source_head(value: str) -> str:
    if re.fullmatch(r'[0-9a-fA-F]{40}', value) is None:
        raise argparse.ArgumentTypeError('--source-head must contain exactly 40 hexadecimal characters')
    return value.lower()


def verify_input_lock(raw: bytes, spec_path: Path, spec: bytes) -> dict:
    lock = json.loads(raw.decode('utf-8', errors='strict'))
    expected = {
        'schema': 'GQ805_SHOP_LIFECYCLE_INPUT_LOCK_V1',
        'official_source_base': OFFICIAL_SOURCE_BASE,
        'spec': {'file': spec_path.name, **identity(spec)},
        'case_count': CASE_COUNT,
        'readonly_controls': READONLY_CONTROLS,
        'original_sources': {
            name: {'bytes': pin[0], 'sha256': pin[1]} for name, pin in PINS.items()
        },
    }
    if lock != expected:
        raise ValueError('INPUT_LOCK schema, spec identity, counts or original source pins differ')
    return lock


def run_command(command: list[str], prefix: Path, timeout: int) -> dict:
    start = time.monotonic()
    timed_out = False
    try:
        run = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
        stdout, stderr, code = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b''
        stderr = (exc.stderr or b'') + b'\nNATIVE_RUNNER_TIMEOUT\n'
        code, timed_out = 124, True
    stdout_path = prefix.with_suffix('.stdout')
    stderr_path = prefix.with_suffix('.stderr')
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    return {'command': command, 'exit_code': code, 'timed_out': timed_out,
            'elapsed_seconds': time.monotonic() - start,
            'stdout': {'file': stdout_path.name, **identity(stdout)},
            'stderr': {'file': stderr_path.name, **identity(stderr)}}


def parse_results(raw: bytes, expected_cases: int, expected_controls: int) -> dict:
    plan, cases, controls, summaries = [], [], [], []
    for line in raw.decode('utf-8', errors='strict').splitlines():
        fields = line.split('\t')
        if fields[0] == 'PLAN':
            if len(fields) != 3 or fields[2] not in {'PASS', 'FAIL'}:
                raise ValueError('malformed case plan')
            plan.append({'name': fields[1], 'baseline_expected': fields[2]})
        elif fields[0] == 'CASE':
            if len(fields) not in {3, 4} or fields[2] not in {'PASS', 'FAIL'}:
                raise ValueError('malformed case result')
            cases.append({'name': fields[1], 'result': fields[2],
                          'message': fields[3] if len(fields) == 4 else None})
        elif fields[0] == 'CONTROLS':
            if len(fields) != 2:
                raise ValueError('malformed readonly-control result')
            controls.append(int(fields[1]))
        elif fields[0] == 'SUMMARY':
            if len(fields) != 5 or fields[4] != 'NOT_STUDIO':
                raise ValueError('invalid Native boundary summary')
            summaries.append({'total': int(fields[1]), 'passed': int(fields[2]), 'failed': int(fields[3])})
        else:
            raise ValueError('unexpected Native stdout line')
    if len(plan) != expected_cases or len(summaries) != 1 or controls != [expected_controls]:
        raise ValueError('case/control count or summary differs from INPUT_LOCK')
    names = [entry['name'] for entry in plan]
    if len(set(names)) != len(names) or names != [entry['name'] for entry in cases]:
        raise ValueError('missing, duplicate or reordered case results')
    summary = summaries[0]
    passed = sum(entry['result'] == 'PASS' for entry in cases)
    if summary != {'total': len(cases), 'passed': passed, 'failed': len(cases) - passed}:
        raise ValueError('summary does not match actual case results')
    return {'plan': plan, 'cases': cases, 'summary': summary, 'preserved_controls': expected_controls}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True,
                        help='unchanged official93 sources directory')
    parser.add_argument('--candidate-source', type=Path, required=True)
    parser.add_argument('--luau', type=Path, required=True)
    parser.add_argument('--luau-compile', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True,
                        help='fresh output directory; must not already exist')
    parser.add_argument('--timeout', type=int, default=60)
    parser.add_argument('--source-head', type=source_head, default=None,
                        help='declared 40-hex GitHub source HEAD; recorded, not independently verified')
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        parser.error('--timeout must be 1..300 seconds')
    spec_path = Path(__file__).with_name('shop_lifecycle.spec.luau')
    spec = read_regular(spec_path)
    lock_path = Path(__file__).with_name('INPUT_LOCK.json')
    lock_raw = read_regular(lock_path)
    lock = verify_input_lock(lock_raw, spec_path, spec)
    original = []
    inputs = {str(lock_path.resolve()): identity(lock_raw)}
    for relative, pin in PINS.items():
        path = args.source_dir / relative
        raw = read_regular(path)
        measured = identity(raw)
        if (measured['bytes'], measured['sha256']) != pin:
            raise ValueError(f'official source identity mismatch: {relative}')
        original.append(raw)
        inputs[str(path.resolve())] = measured
    candidate = read_regular(args.candidate_source)
    if candidate == original[2]:
        raise ValueError('candidate is byte-identical to original negative control')
    inputs[str(args.candidate_source.resolve())] = identity(candidate)
    inputs[str(spec_path.resolve())] = identity(spec)
    binary_inputs = {}
    for path in (args.luau, args.luau_compile):
        binary_inputs[str(path.resolve())] = identity(read_regular(path))
    args.out.mkdir(parents=True, exist_ok=False)
    receipt = {
        'schema': 'GQ805_LOCAL_SHOP_LIFECYCLE_NATIVE_V1',
        'status': 'RUNNING', 'scope': 'UNCONNECTED_LOCAL_PROPOSAL_NOT_STUDIO_NOT_FORMAL_CI',
        'official_source_base': OFFICIAL_SOURCE_BASE,
        'source_head': args.source_head,
        'source_head_verification': 'DECLARED_ONLY_NOT_INDEPENDENTLY_VERIFIED' if args.source_head else None,
        'input_lock': {'path': str(lock_path.resolve()), **identity(lock_raw), 'contents': lock},
        'source_inputs': inputs, 'toolchain_inputs': binary_inputs,
        'runner': identity(Path(__file__).read_bytes()), 'variants': {},
        'limitations': [
            'Mock Roblox object/event boundary; no actual rendering, physics, networking or touch hit testing.',
            'require suspension is deliberately injected; original Catalog/View source bodies do not yield.',
            'WaitForChild dependency return/timeout is controlled explicitly and does not measure engine timing.',
            'Fixture Destroying signals fire eagerly; deferred engine callbacks and script destruction are not certified.',
            'No purchase, wallet, inventory, server authority, Studio, official CI or RC adoption occurred.',
        ],
    }
    failure = None
    try:
        for variant, kiosk in (('baseline', original[2]), ('candidate', candidate)):
            directory = args.out / variant
            directory.mkdir()
            program = spec
            sources = [original[0], original[1], kiosk]
            for marker, source in zip(MARKERS, sources):
                token = marker.encode()
                if program.count(token) != 1:
                    raise ValueError(f'fixture marker count: {marker}')
                program = program.replace(token, source)
            if any(marker.encode() in program for marker in MARKERS):
                raise ValueError('unexpanded source marker')
            if any(program.count(source) != 1 for source in sources):
                raise ValueError('full source body was altered or duplicated')
            program_path = directory / 'shop_lifecycle.native.luau'
            program_path.write_bytes(program)
            result = {'program': identity(program), 'whole_source_bodies': 3,
                      'catalog_and_view_unchanged': True,
                      'kiosk_identity': identity(kiosk)}
            receipt['variants'][variant] = result
            result['compile'] = run_command(
                [str(args.luau_compile.resolve()), '--binary', str(program_path.resolve())],
                directory / 'compile', args.timeout)
            if (result['compile']['exit_code'] != 0 or result['compile']['timed_out']
                    or result['compile']['stderr']['bytes'] != 0):
                raise ValueError(f'{variant} full program failed compilation')
            result['run'] = run_command(
                [str(args.luau.resolve()), str(program_path.resolve())],
                directory / 'run', args.timeout)
            parsed = parse_results((directory / 'run.stdout').read_bytes(),
                                   lock['case_count'], lock['readonly_controls'])
            result.update(parsed)
            if variant == 'baseline':
                matches = all(a['baseline_expected'] == b['result'] for a, b in zip(parsed['plan'], parsed['cases']))
                terminal_lines = [number for number, line in enumerate(program.splitlines(), 1)
                                  if line == TERMINAL_LINE]
                if len(terminal_lines) != 1:
                    raise ValueError('missing or duplicate baseline failure terminal')
                location = f'{program_path.resolve()}:{terminal_lines[0]}'
                expected_terminal = (f'{location}: NATIVE_SHOP_LIFECYCLE_FAILURES={parsed["summary"]["failed"]}\n'
                                     f'stacktrace:\n[C] function error\n{location}\n').encode('utf-8')
                terminal = (directory / 'run.stderr').read_bytes()
                if (not matches or parsed['summary']['failed'] == 0
                        or result['run']['exit_code'] != 1 or result['run']['timed_out']
                        or terminal != expected_terminal):
                    raise ValueError('baseline did not reproduce the declared negative controls exactly')
                result['decision'] = 'EXPECTED_ORIGINAL_FAILURES_REPRODUCED_NOT_CANDIDATE_PASS'
            else:
                if (result['run']['exit_code'] != 0 or result['run']['timed_out']
                        or result['run']['stderr']['bytes'] != 0 or parsed['summary']['failed'] != 0):
                    raise ValueError('candidate did not pass every shared Native case')
                if parsed['plan'] != receipt['variants']['baseline']['plan']:
                    raise ValueError('baseline/candidate case plan differs')
                result['decision'] = 'PASS_LOCAL_NATIVE_ONLY'
        for name, expected in {**inputs, **binary_inputs}.items():
            if identity(read_regular(Path(name))) != expected:
                raise ValueError(f'input changed during execution: {name}')
        receipt['input_invariance'] = True
        receipt['status'] = 'PASS_LOCAL_NATIVE_BASELINE_AND_CANDIDATE_NOT_STUDIO'
    except Exception as exc:
        failure = f'{type(exc).__name__}: {exc}'
        receipt['status'] = 'FAIL'
        receipt['failure'] = failure
    finally:
        receipt_path = args.out / 'RECEIPT.json'
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'receipt': str(receipt_path.resolve()),
                      'variants': {name: value.get('summary') for name, value in receipt['variants'].items()},
                      'failure': failure}, ensure_ascii=False))
    return 1 if failure else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f'NATIVE_RUNNER_REJECTED: {exc}', file=sys.stderr)
        raise SystemExit(2)
