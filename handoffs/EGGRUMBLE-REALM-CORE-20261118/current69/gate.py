#!/usr/bin/env python3
"""Frozen #764 BOMB quality proposal on the actual private69 artifact; no RC writer."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from zipfile import ZipFile

sys.dont_write_bytecode = True
import toolchain

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LOCK_SHA = '2d0345c2af2a8d3bc95877eb36b5f4a8d919bbb6cea9d97a9a829145f40bacb1'
PROJECT = 'EGGRUMBLE_REAL69.project.json'
PLACE = 'EGGRUMBLE_REAL69_PRIVATE.rbxlx'
INTAKE = 'REAL69_LEGACY_INTAKE_RECEIPT.json'
SCOPE_NAMES = ('INPUT_LOCK.json', 'realm_bomb_occlusion.patch',
               'realm_fixture_additions.luau', 'bomb_fixture_additions.luau',
               'bomb_cases_original12.luau', 'bomb_cases_exact_clock.luau',
               'gate.py', 'toolchain.py', 'test_gate.py', 'README.md')
WORKFLOW = '.github/workflows/p0d-gq8-realm-core34.yml'

def require(ok, reason):
    if not ok:
        raise ValueError('RED_GQ764_CURRENT69_' + reason)

def pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def read(path):
    return toolchain.read(path)

def strict_json(raw):
    return toolchain.strict_json(raw)

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def load_lock():
    raw = read(HERE / 'INPUT_LOCK.json')
    require(pin(raw)['sha256'] == LOCK_SHA, 'LOCK_HASH')
    lock = strict_json(raw)
    require(lock['schema'] == 'GQ764_CURRENT69_BOMB_OCCLUSION_INPUTS_V1'
            and len(lock['sources']) == 69 and len(lock['modules_in_load_order']) == 27
            and len(lock['bomb_cases']) == 26, 'LOCK_SHAPE')
    require(pin(read(HERE / 'toolchain.py')) == lock['toolchain_helper']['excerpt'], 'REUSED_TOOLCHAIN_HELPER')
    require(pin(read(HERE / 'realm_bomb_occlusion.patch')) == lock['patch'], 'FROZEN_PATCH')
    for path, expected in lock['bomb_inputs'].items():
        require(pin(read(HERE/path)) == expected, 'FROZEN_BOMB_INPUT:'+path)
    return lock

def verify_owner_files(root, lock):
    rows = {}
    for path, expected in lock['original_owner_files'].items():
        raw = read(root / path)
        compared = raw[:expected['bytes']] if expected['workflow_prefix_only'] else raw
        require(pin(compared) == {k: expected[k] for k in ('bytes', 'sha256')}, 'ORIGINAL_OWNER_FILE:' + path)
        oid = hashlib.sha1(b'blob ' + str(len(compared)).encode() + b'\0' + compared).hexdigest()
        require(oid == expected['git_blob'], 'ORIGINAL_OWNER_BLOB:' + path)
        if expected['workflow_prefix_only']:
            require(raw[len(compared):].startswith(b'  current69-bomb-occlusion:\n'), 'APPEND_JOB_ONLY')
        rows[path] = {'original': pin(compared), 'current': pin(raw)}
    return rows

def scope_snapshot():
    files = [HERE/name for name in SCOPE_NAMES] + [REPO/WORKFLOW]
    return {path.relative_to(REPO).as_posix(): pin(read(path)) for path in files}

def execution_context(kind, git):
    if kind == 'LOCAL_NONCANONICAL':
        require(os.environ.get('GITHUB_ACTIONS') != 'true', 'HOSTED_CANNOT_CLAIM_LOCAL')
        return {'kind': kind, 'canonical_build': False, 'same_head_github_ci': 'NOT_RUN'}
    sha = os.environ.get('GITHUB_SHA', '')
    require(os.environ.get('GITHUB_ACTIONS') == 'true'
            and os.environ.get('GITHUB_REPOSITORY') == 'kk051780/toy-wars-factory'
            and os.environ.get('GITHUB_EVENT_NAME') in ('push', 'pull_request', 'workflow_dispatch')
            and re.fullmatch('[0-9a-f]{40}', sha), 'HOSTED_QA_CONTEXT')
    require(toolchain.git_output(git, REPO, 'rev-parse', 'HEAD').decode().strip() == sha, 'CHECKOUT_GITHUB_SHA')
    for path in scope_snapshot():
        require(toolchain.git_output(git, REPO, 'show', sha+':'+path) == read(REPO/path), 'SCOPE_FILE_NOT_HEAD_BLOB:'+path)
    return {'kind': kind, 'canonical_build': False, 'checkout_sha': sha, 'github_sha': sha,
            'run_id': os.environ.get('GITHUB_RUN_ID'), 'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
            'event': os.environ.get('GITHUB_EVENT_NAME'), 'scope_files_are_exact_head_blobs': True}

def validate_provider(run, artifacts, lock):
    ref = lock['artifact']
    require(run['id'] == ref['run_id'] and run['head_sha'] == lock['official_base']
            and run['head_branch'] == ref['branch'] and run['event'] == ref['event']
            and run['path'] == ref['workflow_path'] and run['status'] == 'completed'
            and run['conclusion'] == 'success' and run['run_attempt'] == ref['run_attempt']
            and run['repository']['full_name'] == 'kk051780/toy-wars-factory', 'OFFICIAL_RUN_METADATA')
    selected = [a for a in artifacts['artifacts'] if a['id'] == ref['id']]
    require(len(selected) == 1, 'EXACT_ARTIFACT_ID')
    artifact = selected[0]
    require(artifact['name'] == ref['name'] and artifact['size_in_bytes'] == ref['zip']['bytes']
            and artifact['expired'] is False and artifact['digest'] == 'sha256:' + ref['zip']['sha256'], 'ARTIFACT_PROVIDER_PIN')
    origin = artifact['workflow_run']
    require(origin['id'] == ref['run_id'] and origin['head_sha'] == lock['official_base']
            and origin['head_branch'] == ref['branch'], 'ARTIFACT_OFFICIAL_LINEAGE')
    return {'run_id': run['id'], 'run_attempt': run['run_attempt'], 'head_sha': run['head_sha'],
            'workflow': run['path'], 'event': run['event'], 'artifact_id': artifact['id'],
            'artifact_name': artifact['name'], 'zip': ref['zip']}

def read_artifact(raw, lock):
    require(pin(raw) == lock['artifact']['zip'], 'ARTIFACT_ZIP_BYTES')
    result = {}
    with ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            name = PurePosixPath(info.filename)
            require(not name.is_absolute() and '..' not in name.parts and '\\' not in info.filename
                    and not info.is_dir() and info.filename not in result
                    and not (info.flag_bits & 1), 'ZIP_ENTRY')
            mode = info.external_attr >> 16
            require(not stat.S_ISLNK(mode), 'ZIP_SYMLINK')
            require(info.filename in lock['artifact']['members'], 'ZIP_UNEXPECTED_MEMBER')
            body = archive.read(info)
            require(pin(body) == lock['artifact']['members'][info.filename], 'ZIP_MEMBER_HASH:' + info.filename)
            result[info.filename] = body
    require(set(result) == set(lock['artifact']['members']), 'ZIP_MEMBER_SET')
    return result

def source_map(archive, lock):
    found = {name.removeprefix('sources/'): body for name, body in archive.items() if name.startswith('sources/')}
    require({p: pin(b) for p,b in found.items()} == lock['sources'], 'EXACT_69_SOURCES')
    intake = strict_json(archive[INTAKE])
    context = intake['execution_context']
    require(intake['build_head'] == lock['official_base'] and intake['source_profile'] == 'REAL69'
            and intake['selected_source_count'] == 69 and context['kind'] == 'OFFICIAL'
            and context['event'] == 'push' and context['canonical_build'] is True
            and str(context['run_id']) == str(lock['artifact']['run_id']), 'ORIGINAL_INTAKE')
    require(pin(archive[PLACE]) == {'bytes': intake['private_place_bytes'], 'sha256': intake['private_place_sha256']}, 'ORIGINAL_PLACE_PIN')
    return found

def project_routes(raw, sources):
    spec = strict_json(raw)
    require(spec['tree']['$className'] == 'DataModel', 'PROJECT_ROOT')
    routes = {}
    def walk(node, parent):
        for name, child in node.items():
            if name.startswith('$'):
                continue
            require(isinstance(child, dict) and '/' not in name, 'PROJECT_NODE')
            route = '/'.join(parent + [name])
            if '$path' in child:
                path = PurePosixPath(child['$path'])
                require(not path.is_absolute() and '..' not in path.parts and path.parts[0] == 'sources', 'PROJECT_SOURCE_PATH')
                relative = path.relative_to('sources').as_posix()
                require(relative in sources and route not in routes, 'PROJECT_SOURCE_ROUTE')
                cls = 'Script' if relative.endswith('.server.luau') else 'LocalScript' if relative.endswith('.client.luau') else 'ModuleScript'
                require(child.get('$className', cls) == cls, 'PROJECT_SOURCE_CLASS')
                routes[route] = {'source': relative, 'class': cls}
            else:
                walk(child, parent + [name])
    walk(spec['tree'], [])
    require(len(routes) == 69 and {x['source'] for x in routes.values()} == set(sources), 'PROJECT_69_ROUTE_COVERAGE')
    return routes

def place_view(raw):
    require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'XML_DECLARATION')
    root = ET.fromstring(raw)
    bodies, layout = {}, {}
    def walk(item, parent):
        props = item.find('Properties')
        require(props is not None, 'XML_PROPERTIES')
        names = [p.text for p in props if p.attrib.get('name') == 'Name']
        require(len(names) == 1 and names[0], 'XML_NAME')
        route = '/'.join(parent + [names[0]])
        require(route not in layout, 'XML_DUPLICATE_ROUTE')
        layout[route] = {'class': item.attrib['class'],
            'properties': [ET.tostring(p, encoding='unicode').strip() for p in props if p.attrib.get('name') != 'Source']}
        source = [p.text or '' for p in props if p.attrib.get('name') == 'Source']
        require(len(source) <= 1, 'XML_DUPLICATE_SOURCE')
        if source:
            bodies[route] = (item.attrib['class'], source[0].encode())
        for child in item.findall('Item'):
            walk(child, parent + [names[0]])
    for item in root.findall('Item'):
        walk(item, [])
    return bodies, layout

def verify_place(raw, routes, sources, original_layout=None):
    bodies, layout = place_view(raw)
    expected = {route: (row['class'], sources[row['source']]) for route,row in routes.items()}
    require(bodies == expected and len(bodies) == 69 and len(layout) == 75, 'PLACE_69_SOURCE_CLASS_75_INSTANCES')
    if original_layout is not None:
        require(layout == original_layout, 'PLACE_NON_SOURCE_PROPERTIES')
    return layout

def canonical_inputs(archive, sources, lock):
    result = {}
    for name, expected in lock['canonical_suites'].items():
        generated = archive[expected['generated_path']]
        receipt = strict_json(archive[expected['receipt_path']])
        require(pin(generated) == expected['generated'] == receipt['generated'], 'CANONICAL_GENERATED:' + name)
        case = generated[-expected['case_suffix']['bytes']:]
        prefix = generated[:-len(case)]
        require(pin(case) == expected['case_suffix'] == receipt['case_file']
                and pin(prefix) == expected['prefix'], 'CANONICAL_SUFFIX_PREFIX:' + name)
        ranges = receipt['full_body_byte_ranges']
        require(ranges == expected['full_body_byte_ranges'] and len(ranges) == 28, 'CANONICAL_28_RANGES')
        for path,row in ranges.items():
            require(pin(sources[path]) == {k: row[k] for k in ('bytes', 'sha256')}
                    and generated[row['start']:row['end']] == sources[path], 'CANONICAL_FULL_BODY:' + path)
        require(receipt['expected_case_names'] == expected['expected_case_names']
                and receipt['exit_code'] == 0 and receipt['exact_complete_pass_vector'] is True, 'CANONICAL_ORACLE')
        result[name] = {'prefix': prefix, 'case': case, 'generated': generated}
    require(len({x['prefix'] for x in result.values()}) == 1, 'CANONICAL_SHARED_PREFIX')
    return result

def assemble_prefix(original_prefix, sources, lock):
    # Reuse the exact canonical wrappers, including their source line metadata.
    # The original reconstruction MUST equal the artifact before a new body is selected.
    order = lock['modules_in_load_order'] + ['LobbyCastleModesPreview.server']
    first = ("\nloadingModule='" + order[0] + "'\n").encode()
    require(original_prefix.count(first) == 1, 'FIXTURE_WRAPPER_ANCHOR')
    fixture = original_prefix[:original_prefix.index(first)]
    code = fixture.decode('utf-8')
    ranges = {}
    for name in order:
        relative = 'ServerScriptService/EGGRUMBLE_' + name + '.luau'
        raw = sources[relative]
        if name == 'LobbyCastleModesPreview.server':
            code += "\ninstallApiObservers()\nloadingModule='Host'\ndo local _=(function()\n"
            label, start = 'Host', code.count('\n') + 1
        else:
            label = name
            code += "\nloadingModule='" + name + "'\n"
            start = code.count('\n') + 3
            code += f"fullSourceRanges.{name}={{first={start},last={start+raw.count(bytes([10]))}}}\n"
            code += 'dependencies.EGGRUMBLE_' + name + '=(function()\n'
            require(code.count('\n') + 1 == start, 'GENERATED_LINE_RANGE')
        first_byte = len(code.encode())
        code += raw.decode('utf-8')
        end_byte = len(code.encode())
        ranges[relative] = {'start': first_byte, 'end': end_byte, **pin(raw)}
        code += '\nend)()end\n' if label == 'Host' else '\nend)()\n'
    code += '\n'
    generated = code.encode()
    for path,row in ranges.items():
        require(generated[row['start']:row['end']] == sources[path]
                and generated.count(sources[path]) == 1, 'GENERATED_28_FULL_BODIES:' + path)
    return generated, ranges, pin(fixture)

def compare_source_maps(actual, expected, reason):
    require(set(actual) == set(expected), reason + '_PATHS')
    require(all(actual[p] == expected[p] for p in expected), reason + '_BYTES')

def snapshot_source(root):
    result = {}
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'SOURCE_SYMLINK')
        if path.is_file():
            require(path.suffix == '.luau', 'SOURCE_EXTRA_FILE')
            result[path.relative_to(root).as_posix()] = read(path)
        else:
            require(path.is_dir(), 'SOURCE_SPECIAL_FILE')
    return result

def write_sources(root, sources, project):
    root.mkdir()
    (root / PROJECT).write_bytes(project)
    for path,raw in sources.items():
        out = root / 'sources' / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)

def process(argv, cwd, log, expected_exit=0):
    log.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    run = subprocess.run([str(x) for x in argv], cwd=cwd, env=toolchain.clean_environment(), capture_output=True, timeout=60)
    log.with_suffix('.stdout.log').write_bytes(run.stdout)
    log.with_suffix('.stderr.log').write_bytes(run.stderr)
    row = {'argv': [str(x) for x in argv], 'cwd': str(cwd), 'started_utc': started,
           'exit': run.returncode, 'stdout': pin(run.stdout), 'stderr': pin(run.stderr)}
    save(log.with_suffix('.json'), row)
    if expected_exit is not None:
        require(run.returncode == expected_exit, 'PROCESS_EXIT:' + str(argv[0]))
    return run, row

def validate_native(exit_code, stdout, stderr, expected_names):
    text = stdout.decode('utf-8')
    rows = [line for line in text.splitlines() if line.startswith('CASE\t')]
    fields = [line.split('\t', 3) for line in rows]
    require(len(fields) == len(expected_names) and all(len(x) == 4 for x in fields)
            and [x[1] for x in fields] == expected_names, 'NATIVE_EXACT_VECTOR')
    require(exit_code == 0 and all(x[2] == 'PASS' for x in fields) and stderr == b'', 'CANONICAL_NATIVE_PASS')
    return rows

def execute_native(binary, native_pin, program, folder, expected_names, ranges):
    folder.mkdir(parents=True)
    path = folder / 'generated.luau'
    path.write_bytes(program)
    require(pin(read(binary)) == native_pin, 'NATIVE_BINARY_BEFORE')
    run, row = process([binary, path], folder, folder / 'process', expected_exit=None)
    rows = validate_native(run.returncode, run.stdout, run.stderr, expected_names)
    require(read(path) == program and pin(read(binary)) == native_pin, 'NATIVE_PROGRAM_BINARY_AFTER')
    receipt = {**row, 'generated': pin(program), 'cases': rows, 'expected_case_names': expected_names,
               'full_body_count': 28, 'full_body_byte_ranges': ranges,
               'realm_and_lss_executed': False, 'expected_failure_control': False}
    save(folder / 'receipt.json', receipt)
    return receipt

def assemble_bomb(canonical, prefix_ranges, sources, lock, oracle):
    values = canonical['combined_clear_los']
    anchor = b'local function guardianHit'
    require(values['case'].count(anchor) == 1, 'BOMB_ORIGINAL_HELPER_ANCHOR')
    helpers = values['case'][:values['case'].index(anchor)]
    expected_case = 'bomb_cases_exact_clock.luau' if oracle['scenario'] == 'OUTSIDE_RADIUS' else 'bomb_cases_original12.luau'
    require(oracle['case_file'] == expected_case, 'BOMB_CASE_VERSION')
    fixtures = b''.join(read(HERE/name) for name in lock['bomb_fixture_order'])
    extra = b'\ndo\n'+sources[lock['lss']]+b'\nend\n\ndo\n'+sources[lock['target']]+b'\nend\n'
    constants = ('local TEST_MODE="'+oracle['mode']+'"\nlocal TEST_SCENARIO="'+oracle['scenario']+'"\n').encode()
    program = values['prefix']+fixtures+extra+helpers+constants+read(HERE/expected_case)
    require(pin(program) == oracle['program'], 'BOMB_ORIGINAL_PROGRAM_PIN')
    ranges = {}
    for path in list(prefix_ranges)+[lock['lss'],lock['target']]:
        raw = sources[path]
        require(program.count(raw) == 1, 'BOMB_BODY_OCCURS_ONCE:'+path)
        start = program.index(raw)
        ranges[path] = {'start':start, 'end':start+len(raw), **pin(raw)}
    require(len(ranges) == 30 and all(ranges[p] == prefix_ranges[p] for p in prefix_ranges),
            'BOMB_UNCHANGED_28_PLUS_FULL_REALM_LSS')
    return program, ranges

def validate_bomb(exit_code, stdout, stderr, program_path, oracle):
    # Exact frozen output prevents a boot/runtime error from masquerading as an expected RED.
    text = stdout.decode('utf-8')
    require(exit_code == oracle['returncode'] and pin(stdout) == oracle['stdout'], 'BOMB_EXACT_OUTPUT_AND_EXIT')
    result = [line for line in text.splitlines() if line.startswith('RESULT\t')]
    require(result == oracle['result_lines'], 'BOMB_EXACT_RESULT')
    observations = []
    for line in text.splitlines():
        if line.startswith('EXPECT\t'):
            fields = line.split('\t')
            require(len(fields) == 5, 'BOMB_OBSERVATION_FORMAT')
            observations.append(dict(zip(('label','status','actual','wanted'), fields[1:])))
    require(observations == oracle['observations'], 'BOMB_EXACT_OBSERVATIONS')
    failures = sum(row['status'] == 'FAIL' for row in observations)
    require((exit_code == 1) == bool(failures) == oracle['source_acceptance_red'], 'BOMB_EXPECTED_SOURCE_RED')
    normalized = stderr.replace(str(program_path).encode(), b'<PROGRAM>')
    require(pin(normalized) == oracle['stderr_normalized'], 'BOMB_STDERR_REASON')
    if failures:
        require(('SOURCE_ACCEPTANCE_RED:'+str(failures)).encode() in stderr, 'BOMB_SOURCE_RED_REASON')
    else:
        require(stderr == b'', 'BOMB_GREEN_STDERR_EMPTY')
    return observations, result, pin(normalized)

def execute_bomb(binary, native_pin, program, folder, ranges, oracle):
    folder.mkdir(parents=True)
    path = folder/'generated.luau'
    path.write_bytes(program)
    require(pin(read(binary)) == native_pin, 'BOMB_NATIVE_BINARY_BEFORE')
    run, row = process([binary, path], folder, folder/'process', expected_exit=None)
    observations, results, normalized_stderr = validate_bomb(run.returncode, run.stdout, run.stderr, path, oracle)
    require(read(path) == program and pin(read(binary)) == native_pin, 'BOMB_PROGRAM_BINARY_AFTER')
    receipt = {**row, 'generated':pin(program), 'reference_program_exact':True,
        'case_file':oracle['case_file'], 'observations':observations, 'result_lines':results,
        'stderr_normalized': normalized_stderr, 'full_body_count':30, 'full_body_byte_ranges':ranges,
        'realm_and_lss_executed': True, 'expected_failure_control':oracle['source_acceptance_red'],
        'mode':oracle['mode'], 'scenario':oracle['scenario']}
    save(folder/'receipt.json',receipt)
    return receipt


def safe_output(output, inputs):
    output = toolchain.safe_root(output)
    require(not output.exists(), 'OUTPUT_MUST_BE_NEW')
    for path in inputs:
        actual = toolchain.safe_root(path)
        require(output != actual and not output.is_relative_to(actual)
                and not actual.is_relative_to(output), 'OUTPUT_INPUT_OVERLAP')
    return output

def run_gate(args):
    lock = load_lock()
    scope_before = scope_snapshot()
    context = execution_context(args.context, args.git)
    owner_before = verify_owner_files(REPO, lock)
    source = toolchain.safe_root(args.luau_source)
    output = safe_output(args.out, [source, args.artifact_zip, args.rojo_zip, HERE])
    run_raw, artifact_raw = read(args.run_metadata), read(args.artifact_metadata)
    provider = validate_provider(strict_json(run_raw), strict_json(artifact_raw), lock)
    archive_raw = read(args.artifact_zip)
    archive = read_artifact(archive_raw, lock)
    original = source_map(archive, lock)
    routes = project_routes(archive[PROJECT], original)
    original_layout = verify_place(archive[PLACE], routes, original)
    canonical = canonical_inputs(archive, original, lock)
    original_prefix = canonical['combined_clear_los']['prefix']
    rebuilt_original, original_ranges, fixture_pin = assemble_prefix(original_prefix, original, lock)
    require(rebuilt_original == original_prefix, 'ORIGINAL_PREFIX_BYTE_EXACT')
    rojo_archive = read(args.rojo_zip)
    require(pin(rojo_archive) == lock['rojo']['zip'], 'ROJO_ZIP')
    with ZipFile(io.BytesIO(rojo_archive)) as z:
        require(z.namelist() == ['rojo'], 'ROJO_ARCHIVE_MEMBER')
        rojo_raw = z.read('rojo')
    require(pin(rojo_raw) == lock['rojo']['binary'], 'ROJO_BINARY')
    output.mkdir(parents=True)
    save(output / 'provider.json', provider)
    (output / 'run_metadata.json').write_bytes(run_raw)
    (output / 'artifact_metadata.json').write_bytes(artifact_raw)
    build_log = output / 'toolchain_evidence'; build_log.mkdir()
    binary, built, tree_before = toolchain.build_repl(source, output / 'luau-build', build_log, lock,
        args.cmake, args.ninja, args.git, args.cc, args.cxx)
    compiler = output / 'luau-build/luau-compile'
    require(not compiler.exists(), 'COMPILER_MUST_BE_NEW')
    started_ns = time.time_ns()
    compiler_command = toolchain.command_log([args.cmake, '--build', output / 'luau-build', '--target',
         'Luau.Compile.CLI', '--parallel', '2'], build_log, 'compiler_build', 900)
    require(compiler.is_file() and os.access(compiler, os.X_OK) and compiler.stat().st_mtime_ns >= started_ns
            and b'Linking CXX executable luau-compile' in read(build_log/'compiler_build.stdout.log'), 'FRESH_COMPILER')
    compiler_pin = pin(read(compiler))
    native_pin = pin(read(binary))
    rojo = output / 'rojo'; rojo.write_bytes(rojo_raw); rojo.chmod(0o755)
    on, off = output / 'on', output / 'off'
    write_sources(on, original, archive[PROJECT])
    patch = HERE / 'realm_bomb_occlusion.patch'
    patch_commands = []
    for label, arguments in [('forward_check', ['--check']), ('forward_apply', [])]:
        _, row = process([args.git, 'apply', *arguments, patch], on/'sources', output/'patch_logs'/label)
        patch_commands.append(row)
    selected = snapshot_source(on / 'sources')
    require(set(selected) == set(original) and {p for p in original if selected[p] != original[p]} == {lock['target']}, 'ONLY_ONE_OF_69_CHANGED')
    require(pin(selected[lock['target']]) == lock['candidate']
            and len(selected[lock['target']])-len(original[lock['target']]) == lock['delta_bytes'], 'FROZEN_695_CANDIDATE')
    write_sources(off, selected, archive[PROJECT])
    for label, arguments in [('inverse_check', ['--reverse', '--check']), ('inverse_apply', ['--reverse'])]:
        _, row = process([args.git, 'apply', *arguments, patch], off/'sources', output/'patch_logs'/label)
        patch_commands.append(row)
    restored = snapshot_source(off / 'sources')
    compare_source_maps(restored, original, 'ACTUAL_INVERSE_ALL69')
    compile_rows, places = [], {}
    for variant, folder, sources in [('on', on, selected), ('off', off, restored)]:
        for index,path in enumerate(sorted(sources)):
            _, row = process([compiler, '--null', folder/'sources'/path], folder, output/'compile_logs'/f'{variant}_{index:02d}')
            compile_rows.append({'variant': variant, 'source': path, **row})
        _, row = process([rojo, 'build', folder/PROJECT, '-o', folder/PLACE], folder, output/'build_logs'/variant)
        raw = read(folder / PLACE)
        verify_place(raw, routes, sources, original_layout)
        places[variant] = {'place': pin(raw), 'source_count': 69, 'instance_count': 75,
            'source_class_exact': True, 'non_source_properties_exact': True, 'build': row}
    require(read(off/PLACE) == archive[PLACE], 'INVERSE_PLACE_EXACT_OFFICIAL_BYTES')
    # Realm is absent from the preserved 28-body canonical prefix.
    require(lock['target'] not in original_ranges and lock['lss'] not in original_ranges,
            'CANONICAL_REALM_NOT_EXECUTED_LIMIT')
    candidate_prefix, candidate_ranges, candidate_fixture_pin = assemble_prefix(original_prefix, selected, lock)
    require(candidate_prefix == original_prefix and candidate_ranges == original_ranges
            and candidate_fixture_pin == fixture_pin, 'CANONICAL_28_BODIES_AND_FIXTURE_UNCHANGED')
    native_rows = []
    for variant, sources in [('official', original), ('candidate', selected)]:
        for name, values in canonical.items():
            expected = lock['canonical_suites'][name]
            program = original_prefix + values['case']
            require(program == values['generated'], 'UNCHANGED_CANONICAL_GENERATED_PROGRAM')
            row = execute_native(binary, native_pin, program, output/'native'/variant/name,
                                 expected['expected_case_names'], original_ranges)
            native_rows.append({'variant': variant, 'suite': name, **row})
        for oracle in lock['bomb_cases']:
            if oracle['variant'] != variant:
                continue
            program, ranges = assemble_bomb(canonical, original_ranges, sources, lock, oracle)
            row = execute_bomb(binary, native_pin, program, output/'native'/oracle['name'], ranges, oracle)
            native_rows.append({'variant': variant, 'suite': oracle['scenario'], **row})
    compare_source_maps(snapshot_source(on/'sources'), selected, 'ON_UNCHANGED_AFTER_NATIVE')
    compare_source_maps(snapshot_source(off/'sources'), original, 'OFF_UNCHANGED_AFTER_NATIVE')
    require(verify_owner_files(REPO, lock) == owner_before, 'OWNER_FILES_CHANGED')
    require(scope_snapshot() == scope_before and execution_context(args.context, args.git) == context, 'SCOPE_OR_CONTEXT_CHANGED')
    require(read(args.artifact_zip) == archive_raw and read(args.rojo_zip) == rojo_archive
            and read(args.run_metadata) == run_raw and read(args.artifact_metadata) == artifact_raw, 'EXTERNAL_INPUT_CHANGED')
    require(pin(read(binary)) == native_pin and pin(read(compiler)) == compiler_pin
            and pin(read(rojo)) == lock['rojo']['binary'], 'TOOL_BINARY_CHANGED')
    require(toolchain.verify_clean_source(source, Path(args.git).resolve(), lock['toolchain']) == tree_before, 'TOOLCHAIN_SOURCE_CHANGED')
    built['binary_after_suites'] = native_pin
    built['compiler'] = {'path': str(compiler), **compiler_pin, 'fresh_target_build': compiler_command}
    save(build_log / 'build_receipt.json', built)
    receipt = {'schema': 'GQ764_CURRENT69_SOURCE_NATIVE_BUILD_RECEIPT_V1',
        'status': 'PASS_LOCAL_OR_HOSTED_SOURCE_QA_ONLY', 'official_base': lock['official_base'],
        'owner_pr': 764, 'candidate_target': lock['target'], 'candidate': lock['candidate'],
        'source_delta_bytes': 695, 'source_count': 69, 'changed': 1, 'other_sources_exact': 68,
        'provider': provider, 'owner_preservation': owner_before, 'patch_commands': patch_commands,
        'compile_count': len(compile_rows), 'compile_results': compile_rows, 'places': places,
        'actual_inverse_sources': 69, 'actual_inverse_place_official_exact': True,
        'fixture_prefix': fixture_pin, 'native_program_count': len(native_rows), 'native_runs': native_rows,
        'canonical_original': '10+7 PASS', 'canonical_candidate': '10+7 PASS',
        'bomb_original': lock['bomb_summary']['official'], 'bomb_candidate': lock['bomb_summary']['candidate'],
        'classification': lock['classification'], 'original_core34_hosted_job': 'NOT_RUN',
        'whole_hosted_workflow': 'NOT_RUN',
        'fresh_toolchain_receipt': pin(read(build_log/'build_receipt.json')),
        'runner': pin(read(Path(__file__))), 'input_lock': pin(read(HERE/'INPUT_LOCK.json')),
        'execution_context': context, 'scope_files_before_after': scope_before,
        'canonical_build': False, 'formal_rc_adopted': False, 'registered_approval': False,
        'github_writes': 0, 'studio': 'NOT_TESTED', 'android': 'NOT_TESTED', 'fun': 'NO_GO',
        'limitations': lock['limitations']}
    require(len(native_rows) == 30 and len(compile_rows) == 138, 'COMPLETE_QA_COUNTS')
    save(output / 'receipt.json', receipt)
    print('GQ764_CURRENT69_SOURCE_NATIVE_ONLY_PASS ' + json.dumps({
        'canonical': 'old/new 10+7', 'BOMB13': 'old5/13 new13/13; old164/180 new180/180 observations',
        'compile': 138, 'inverse69': True, 'candidate': lock['candidate'], 'on_place': places['on']['place']}), flush=True)
    return receipt

def main():
    parser = argparse.ArgumentParser()
    for name in ['artifact-zip', 'run-metadata', 'artifact-metadata', 'luau-source', 'rojo-zip', 'out']:
        parser.add_argument('--'+name, required=True, type=Path)
    for name in ['cmake', 'ninja', 'git', 'cc', 'cxx']:
        parser.add_argument('--'+name, default=shutil.which('c++' if name == 'cxx' else name), type=Path)
    parser.add_argument('--context', choices=['LOCAL_NONCANONICAL', 'GITHUB_NONCANONICAL_QA'], required=True)
    args = parser.parse_args()
    require(all(getattr(args,n) is not None for n in ['cmake','ninja','git','cc','cxx']), 'BUILD_TOOLS_AVAILABLE')
    run_gate(args)

if __name__ == '__main__':
    main()
