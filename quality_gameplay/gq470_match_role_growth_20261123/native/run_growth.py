#!/usr/bin/env python3
"""Fixed S1A ON/H93/OFF source contract; fresh Native build, never engine approval."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
REPO = PACKAGE.parents[1]
FROZEN = REPO / 'quality_gameplay/gq470_union22_real69_20261122/native'
INPUT_LOCK_SHA256 = 'b4157db7865fdc68756d64e58393be0c7c2ed2f88159026fa39a8664eaa5f533'
PACKAGE_PREFIX = 'quality_gameplay/gq470_match_role_growth_20261123/'
NEW_PATHS = [PACKAGE_PREFIX + path for path in (
    'README.md', 'growth_patch.json', 'source_lock.json', 'apply_growth.py',
    'native/growth_cases.luau', 'native/run_growth.py', 'native/INPUT_LOCK.json')]
NEW_PATHS += ['tests/test_gq470_match_role_growth_20261123.py', '.github/workflows/gq470-match-role-growth.yml']


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


apply_source = module('s1a_exact_source_applier', PACKAGE / 'apply_growth.py')
require, read, identity = apply_source.require, apply_source.read, apply_source.identity


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def repository_snapshot(frozen, git, head, contract):
    require(frozen.git_output(git, REPO, 'rev-parse', 'HEAD').decode().strip() == head, 'ACTUAL_REPO_HEAD')
    require(not frozen.git_output(git, REPO, 'status', '--porcelain=v1', '--untracked-files=all'), 'REPOSITORY_NOT_CLEAN')
    result = {}
    for relative in sorted(set(NEW_PATHS) | set(contract['repository_inputs'])):
        row = frozen.git_output(git, REPO, 'ls-tree', '-z', head, '--', relative)
        require(row.endswith(b'\0') and row.count(b'\0') == 1, 'HEAD_FILE_MISSING:' + relative)
        metadata, name = row[:-1].split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        require(name.decode() == relative and mode in ('100644', '100755') and kind == 'blob', 'HEAD_FILE_TYPE')
        committed = frozen.git_output(git, REPO, 'show', head + ':' + relative)
        actual = read(REPO / relative)
        require(actual == committed, 'PHYSICAL_BYTES_DIFFER_FROM_HEAD:' + relative)
        actual_mode = '100755' if (REPO / relative).stat().st_mode & 0o111 else '100644'
        require(actual_mode == mode, 'PHYSICAL_MODE_DIFFER_FROM_HEAD:' + relative)
        result[relative] = {'git_blob': oid, 'mode': mode, **identity(actual)}
    return result


def load_inputs():
    raw = read(HERE / 'INPUT_LOCK.json')
    require(identity(raw)['sha256'] == INPUT_LOCK_SHA256, 'NATIVE_LOCK_CHANGED')
    contract = apply_source.unique_json(raw)
    require(contract['schema'] == 'GQ470_S1A_FIXED_NATIVE_ON_H93_OFF_V1', 'NATIVE_SCHEMA')
    for relative, pin in contract['repository_inputs'].items():
        apply_source.safe_relative(relative)
        require(identity(read(REPO / relative)) == pin, 'REPOSITORY_INPUT_CHANGED:' + relative)
    frozen = module('unchanged_union22_build_and_fixture_helpers', FROZEN / 'run_profile.py')
    old = frozen.load_lock()
    frozen.fixture_snapshot(old)
    source_lock, patch = apply_source.load_contract()
    require(old['sources'] == source_lock['sources_before'], 'HISTORICAL_SOURCE_LOCK_MISMATCH')
    packed = read(HERE / 'growth_cases.luau')
    require(identity(packed) == contract['case_pack'], 'FIXED_CASE_PACK_CHANGED')
    sections, cursor = {}, 0
    for name, pin in contract['sections'].items():
        begin = ('-- GQ470_SECTION_BEGIN ' + name + '\n').encode()
        end = ('-- GQ470_SECTION_END ' + name + '\n').encode()
        require(packed.count(begin) == packed.count(end) == 1, 'SECTION_MARKER_COUNT:' + name)
        start = packed.index(begin)
        stop = packed.index(end)
        require(start == cursor and stop > start, 'SECTION_ORDER_OR_EXTRA_INPUT:' + name)
        body = packed[start + len(begin):stop]
        require(identity(body) == pin, 'SECTION_CHANGED:' + name)
        sections[name] = body
        cursor = stop + len(end)
    require(cursor == len(packed), 'TRAILING_CASE_INPUT')
    helpers = read(FROZEN / 'combined_cases_clear_los.luau').split(b'local ok,result=pcall(function()', 1)[0]
    require(identity(helpers) == contract['original_helper_prefix'], 'ORIGINAL_HELPERS_CHANGED')
    return contract, sections, frozen, old, source_lock, helpers


def server_program(frozen, old, sections, helpers, sources, variant, extra_modules=(), extra_engine=(), case_section='SERVER_CASES'):
    code = bytearray()
    def append(value):
        code.extend(value.encode() if isinstance(value, str) else value)
    for name in old['fixture_order']:
        append(read(FROZEN / 'fixtures' / name)); append('\n')
    append(sections['SERVER_ENGINE']); append('\n')
    for name in extra_engine:
        append(sections[name]); append('\n')
    order = list(old['modules_in_load_order']) + list(extra_modules) + ['Host']
    ranges, bodies = {}, {}
    for name in order:
        relative = 'ServerScriptService/EGGRUMBLE_' + ('LobbyCastleModesPreview.server' if name == 'Host' else name) + '.luau'
        raw = read(sources / relative)
        if name == 'Host':
            append('\ninstallApiObservers()\n')
        append("\nloadingModule='" + name + "'\n")
        first = bytes(code).count(b'\n') + 3
        last = first + raw.count(b'\n') - int(raw.endswith(b'\n'))
        append(f'fullSourceRanges.{name}={{first={first},last={last}}}\n')
        append('do local _=(function()\n' if name == 'Host' else 'dependencies.EGGRUMBLE_' + name + '=(function()\n')
        require(bytes(code).count(b'\n') + 1 == first, 'SERVER_SOURCE_RANGE')
        start = len(code); append(raw)
        bodies[relative] = {'start': start, 'end': len(code), **identity(raw)}
        ranges[name] = {'first': first, 'last': last}
        append('\nend)() end\n' if name == 'Host' else '\nend)()\n')
    append(helpers); append("\nlocal AUDIT_VARIANT='" + variant + "'\n")
    append(sections[case_section]); append('\n')
    program = bytes(code)
    verify_bodies(program, bodies, sources, 28 + len(extra_modules))
    return program, ranges, bodies


def verify_bodies(program, bodies, sources, count):
    require(len(bodies) == count, 'FULL_BODY_COUNT')
    for relative, row in bodies.items():
        require(program[row['start']:row['end']] == read(sources / relative), 'FULL_BODY_CHANGED:' + relative)


# The UI assembler below is generated once from the independently exercised
# full-31-body assembler, then reviewed and committed with this exact runner.
def assemble_ui(runner, frozen_lock, baseline_root, selected_root,
                observers_bytes, ui_boundary_bytes, acceptance_boundary_bytes,
                cases_bytes, generic_api_bytes):
    """Return (program_bytes, receipt_fields), with candidate-green fixed.

    `runner` is the frozen UNION22 run_profile module; only its read-only
    helpers and HERE directory are used. Four original engine bodies and the
    original helper prefix are read from that runner's pinned own directory.
    All newly added sections are explicit bytes; no scratch lookup is hidden.
    The caller owns saving, execution, negative controls, and result parsing.
    """
    for name, value in (
        ("observers", observers_bytes), ("ui_engine", ui_boundary_bytes),
        ("ui_acceptance_engine", acceptance_boundary_bytes),
        ("ui_cases", cases_bytes), ("generic_api", generic_api_bytes),
    ):
        runner.require(type(value) is bytes and value, "UI_SECTION_BYTES_REQUIRED:" + name)
    baseline_root = runner.safe_root(baseline_root)
    selected_root = runner.safe_root(selected_root)
    baseline = runner.source_snapshot(baseline_root)
    selected = runner.source_snapshot(selected_root)
    runner.require(len(baseline) == 69 and baseline == frozen_lock["sources"], "UI_EXACT_H93_69_REQUIRED")
    runner.require(set(selected) == set(baseline), "UI_EXACT_69_PATHS_REQUIRED")
    mutable = {
        "ServerScriptService/EGGRUMBLE_SwarmCombat.luau",
        "ServerScriptService/EGGRUMBLE_HeroSilhouetteArt.server.luau",
        "ServerScriptService/EGGRUMBLE_MatchResultService.luau",
        "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau",
    }
    changed = sorted(path for path in selected if selected[path] != baseline[path])
    runner.require(set(changed).issubset(mutable), "UI_OUT_OF_FOUR_SOURCE_SCOPE")
    frozen_fixtures = runner.fixture_snapshot(frozen_lock)
    fixtures = {}
    for name in frozen_lock["fixture_order"]:
        raw = runner.read(runner.HERE / "fixtures" / name)
        runner.require(runner.identity(raw) == frozen_lock["fixtures"][name], "UI_FIXTURE_PIN:" + name)
        fixtures[name] = raw
    helper_path = frozen_lock["case_files"]["combined_clear_los"]
    original_case = runner.read(runner.HERE / helper_path)
    runner.require(runner.identity(original_case) == frozen_lock["suites"]["combined_clear_los"]["case"],
                   "UI_ORIGINAL_HELPER_CONTAINER_PIN")
    separator = b"local ok,result=pcall(function()"
    runner.require(original_case.count(separator) == 1, "UI_HELPER_BOUNDARY")
    helpers = original_case.split(separator, 1)[0]
    runner.require(len(helpers) > 1000, "UI_UNCHANGED_TEST_HELPERS_MISSING")

    legacy_specs = (
        ("HeroSilhouetteArt", "ServerScriptService/EGGRUMBLE_HeroSilhouetteArt.server.luau", 352, 368, False),
        ("HudIntelRuntime", "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau", 609, 672, True),
    )
    legacy_regions, legacy_diagnostics = {}, {}
    for name, relative, low, high, require_unchanged in legacy_specs:
        base_raw = runner.read(baseline_root / relative)
        fragment = b"".join(base_raw.splitlines(keepends=True)[low-1:high])
        raw = runner.read(selected_root / relative)
        runner.require(fragment and base_raw.count(fragment) == 1, "UI_LEGACY_BASE_BLOCK:" + name)
        occurrences = raw.count(fragment)
        if require_unchanged:
            runner.require(occurrences == 1, "UI_LEGACY_HUD_609_672_MUST_REMAIN_BYTE_IDENTICAL")
        regions = []
        if occurrences == 1:
            first = raw[:raw.index(fragment)].count(b"\n") + 1
            regions.append({"first": first, "last": first + fragment.count(b"\n") - int(fragment.endswith(b"\n"))})
        legacy_regions[name] = regions
        legacy_diagnostics[name] = {
            "source": relative, "baseline_lines": [low, high], "fragment": runner.identity(fragment),
            "candidate_occurrences": occurrences, "candidate_regions": regions,
            "byte_identity_required": require_unchanged, "hero_cleanup_exemption": False,
        }

    modules = [(name, "ServerScriptService/EGGRUMBLE_" + name + ".luau", "module")
               for name in frozen_lock["modules_in_load_order"]]
    runner.require(len(modules) == 27 and len(set(name for name, _, _ in modules)) == 27,
                   "UI_EXACT_27_BASE_MODULES")
    modules += [
        ("Host", "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.server.luau", "server"),
        ("HeroSilhouetteArt", "ServerScriptService/EGGRUMBLE_HeroSilhouetteArt.server.luau", "server"),
        ("HudPresentationPolicy", "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy.luau", "module"),
        ("HudIntelRuntime", "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau", "client"),
    ]
    code = bytearray()
    line_count = 0

    def append(value):
        nonlocal line_count
        raw = value.encode("utf-8") if isinstance(value, str) else value
        code.extend(raw)
        line_count += raw.count(b"\n")

    def append_blob(name, raw, spans):
        start, first = len(code), line_count + 1
        append(raw)
        spans[name] = {"start": start, "end": len(code), "first": first,
                       "last": first + raw.count(b"\n") - int(raw.endswith(b"\n")),
                       **runner.identity(raw)}

    fixture_spans, extension_spans, source_spans, source_lines = {}, {}, {}, {}
    for name in frozen_lock["fixture_order"]:
        append_blob(name, fixtures[name], fixture_spans); append("\n")
    for name, raw in (
        ("observers", observers_bytes), ("ui_engine", ui_boundary_bytes),
        ("ui_acceptance_engine", acceptance_boundary_bytes), ("generic_api", generic_api_bytes),
    ):
        append_blob(name, raw, extension_spans); append("\n")
    for name, regions in legacy_regions.items():
        literal = ",".join("{first=" + str(row["first"]) + ",last=" + str(row["last"]) + "}" for row in regions)
        append("UIAcceptanceEngine.legacyRegions." + name + "={" + literal + "}\n")
    for name, relative, kind in modules:
        raw = runner.read(selected_root / relative)
        runner.require(runner.identity(raw) == selected[relative], "UI_SOURCE_CHANGED_DURING_ASSEMBLY:" + relative)
        if name == "Host":
            append("\ninstallApiObservers()\n")
        append("\nloadingModule='" + name + "'\n")
        append("UIAudit.realm='" + ("client" if kind == "client" else "server") + "'\n")
        first = line_count + 3
        last = first + raw.count(b"\n") - int(raw.endswith(b"\n"))
        append(f"fullSourceRanges.{name}={{first={first},last={last}}}\n")
        append("dependencies.EGGRUMBLE_" + name + "=(function()\n" if kind == "module" else "do local _=(function()\n")
        runner.require(line_count + 1 == first, "UI_SOURCE_RANGE_START:" + name)
        append_blob(relative, raw, source_spans)
        source_lines[name] = {"first": first, "last": last}
        append("\nend)()\n" if kind == "module" else "\nend)() end\n")
    append("\nUIAudit.realm='server'\n")
    append_blob("unchanged_helper_prefix", helpers, extension_spans); append("\n")
    append("local UI_ACCEPTANCE_EXPECT='candidate-green'\n")
    append_blob("ui_cases", cases_bytes, extension_spans); append("\n")
    program = bytes(code)
    runner.require(len(source_spans) == 31, "UI_ALL31_FULL_BODIES_REQUIRED")
    for relative, span in source_spans.items():
        runner.require(program[span["start"]:span["end"]] == runner.read(selected_root / relative),
                       "UI_SOURCE_BODY_REWRITTEN:" + relative)
    for name, span in fixture_spans.items():
        runner.require(program[span["start"]:span["end"]] == fixtures[name], "UI_FIXTURE_BODY_REWRITTEN:" + name)
    return program, {
        "schema": "GQ470_FULL31_UI_PURE_ASSEMBLY_V1", "expectation_mode": "candidate-green",
        "full_source_bodies": 31, "source_count_pinned": 69,
        "baseline_source_profile": baseline, "selected_source_profile": selected,
        "candidate_changed_paths": changed, "frozen_fixtures": frozen_fixtures,
        "full_body_byte_ranges": source_spans, "source_line_ranges": source_lines,
        "fixture_byte_ranges": fixture_spans, "extension_byte_ranges": extension_spans,
        "legacy_callback_regions": legacy_diagnostics,
        "unchanged_helper_source": helper_path, "generated": runner.identity(program),
        "candidate_incomplete_message": "candidate must satisfy every reachable UI requirement",
        "writes_files": False, "executes_native": False,
    }


def ui_program(frozen, old, sections, helpers, baseline_sources, sources):
    program, metadata = assemble_ui(frozen, old, baseline_sources, sources,
        sections['UI_OBSERVERS'], sections['UI_ENGINE'], sections['UI_ACCEPT_ENGINE'],
        sections['UI_CASES'], sections['UI_GENERIC_API'])
    require(metadata['expectation_mode'] == 'candidate-green', 'FIXED_UI_CRITERIA')
    return program, metadata['source_line_ranges'], metadata['full_body_byte_ranges']



def vector(lines, prefix):
    selected = [line for line in lines if line.startswith(prefix + '\t')]
    parts = [line.split('\t', 3) for line in selected]
    require(all(len(row) == 4 for row in parts), 'MALFORMED_' + prefix)
    return [[row[1], row[2]] for row in parts], selected


def run_fixed(name, program, ranges, bodies, binary, binary_pin, sources, expected, output, frozen, old, source_profile):
    target = output / name
    target.mkdir(exist_ok=False)
    before = frozen.source_snapshot(sources)
    require(before == source_profile, 'SUITE_EXACT69_PROFILE:' + name)
    for relative, span in bodies.items():
        require(identity(program[span['start']:span['end']]) == source_profile[relative], 'SUITE_BODY_PROFILE:' + relative)
    generated = target / 'generated.luau'
    generated.write_bytes(program)
    require(identity(read(binary)) == binary_pin, 'NATIVE_CHANGED_BEFORE_SUITE')
    result = subprocess.run([str(binary), str(generated)], env=frozen.clean_environment(), capture_output=True, timeout=60)
    (target / 'stdout.log').write_bytes(result.stdout)
    (target / 'stderr.log').write_bytes(result.stderr)
    lines = result.stdout.decode('utf-8').splitlines()
    cases, case_lines = vector(lines, 'CASE')
    expectations, expectation_lines = vector(lines, 'EXPECTATION')
    receipt = {
        'schema': 'GQ470_S1A_FIXED_NATIVE_SUITE_V1', 'status': 'FAIL_NO_ADMISSION',
        'suite': name, 'native_exit': result.returncode, 'expected_exit': expected['exit'],
        'expected_cases': expected['cases'], 'actual_cases': cases,
        'expected_expectations': expected.get('expectations', []), 'actual_expectations': expectations,
        'full_source_bodies_executed': len(bodies), 'source_count_pinned': len(before),
        'source_profile': before, 'source_line_ranges': ranges, 'full_body_byte_ranges': bodies,
        'generated': identity(program), 'native': binary_pin,
        'stdout': identity(result.stdout), 'stderr': identity(result.stderr),
        'cases': case_lines, 'expectations': expectation_lines,
        'observations': [line for line in lines if line.startswith(('OBSERVATION\t', 'METRIC\t'))],
        'scope': 'NATIVE_ENGINE_BOUNDARY_ONLY_NOT_ROBLOX_STUDIO',
    }
    write_json(target / 'receipt.json', receipt)
    require(result.returncode == expected['exit'], 'EXIT_VECTOR:' + name)
    require(cases == expected['cases'], 'EXACT_CASE_VECTOR:' + name)
    require(expectations == expected.get('expectations', []), 'EXACT_EXPECTATION_VECTOR:' + name)
    if expected['exit'] == 0:
        require(result.stderr == b'', 'SUCCESS_WITH_STDERR:' + name)
    else:
        marker = expected['failure_marker'].encode()
        require(marker in result.stderr + result.stdout, 'EXPECTED_FAILURE_REASON:' + name)
    require(not any(line.startswith('WARN\t') for line in lines), 'NATIVE_WARNING:' + name)
    require(frozen.source_snapshot(sources) == before, 'SOURCE_MUTATION:' + name)
    require(read(generated) == program and identity(read(binary)) == binary_pin, 'PROGRAM_OR_BINARY_MUTATION:' + name)
    frozen.fixture_snapshot(old)
    receipt['status'] = 'PASS_FIXED_NEGATIVE_CONTROL' if expected['exit'] else 'PASS_NATIVE_ONLY'
    receipt['source_inputs_unchanged'] = True
    write_json(target / 'receipt.json', receipt)
    print(name + ': ' + receipt['status'] + f' ({len(cases)} cases, {len(expectations)} expectations)', flush=True)
    return identity(read(target / 'receipt.json'))


def verify_place(place, baseline_place, sources, baseline_sources):
    tree, baseline = ET.fromstring(read(place)), ET.fromstring(read(baseline_place))
    classes = Counter(item.attrib['class'] for item in tree.iter('Item'))
    require(sum(classes.values()) == 75 and classes['ModuleScript'] == 47
            and classes['Script'] == 12 and classes['LocalScript'] == 10, 'PLACE_CLASS_COUNT')
    embedded = Counter()
    for item in tree.iter('Item'):
        prop = item.find("Properties/*[@name='Source']")
        if prop is not None:
            embedded[(item.attrib['class'], (prop.text or '').encode())] += 1
    selected = Counter()
    for relative in apply_source.source_snapshot(sources):
        kind = 'Script' if relative.endswith('.server.luau') else 'LocalScript' if relative.endswith('.client.luau') else 'ModuleScript'
        selected[(kind, read(sources / relative))] += 1
    require(embedded == selected and sum(embedded.values()) == 69, 'PLACE_FULL_SOURCE_BYTES')
    # The exact pinned baseline XML supplies each concrete Instance position.
    # Replace only its four unique old Source bodies with their selected bytes.
    # Comparing the entire expected tree also rejects same-class Source swaps.
    for relative in sorted(apply_source.CHANGED):
        previous = read(baseline_sources / relative).decode('utf-8')
        replacement = read(sources / relative).decode('utf-8')
        matches = [prop for item in baseline.iter('Item')
                   for prop in [item.find("Properties/*[@name='Source']")]
                   if prop is not None and prop.text == previous]
        require(len(matches) == 1, 'BASELINE_INSTANCE_SOURCE_NOT_UNIQUE:' + relative)
        matches[0].text = replacement
    require(ET.tostring(tree) == ET.tostring(baseline), 'PLACE_INSTANCE_SOURCE_OR_STRUCTURE_CHANGED')
    return {'place': identity(read(place)), 'classes': dict(classes), 'exact_embedded_sources': 69,
            'nonsource_structure_unchanged': True, 'source_instance_binding_exact': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline-root', 'on-root', 'off-root', 'artifact-zip', 'luau-source', 'build-dir',
                 'out', 'cmake', 'ninja', 'git', 'cc', 'cxx', 'rojo'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--head', required=True)
    args = parser.parse_args()
    contract, sections, frozen, old, source_lock, helpers = load_inputs()
    repository_before = repository_snapshot(frozen, args.git, args.head, contract)
    require(identity(read(args.artifact_zip)) == source_lock['official_input']['zip'], 'OFFICIAL_ARTIFACT_ZIP')
    inputs = {'H93': args.baseline_root, 'ON': args.on_root, 'OFF': args.off_root}
    roots = [apply_source.safe_root(x) for x in [*inputs.values(), args.luau_source, args.build_dir, args.out]]
    require(all(not a.is_relative_to(b) and not b.is_relative_to(a)
                for index, a in enumerate(roots) for b in roots[index + 1:]), 'GATE_DIRECTORY_OVERLAP')
    before = {}
    for label, root in inputs.items():
        before[label] = frozen.source_snapshot(root / 'sources')
        require(before[label] == source_lock['sources_after' if label == 'ON' else 'sources_before'], 'EXACT69_' + label)
        require(identity(read(root / apply_source.PROJECT)) == {k: source_lock['project'][k] for k in ('bytes', 'sha256')}, 'PROJECT_' + label)
    require(identity(read(args.baseline_root / 'EGGRUMBLE_REAL69_PRIVATE.rbxlx')) == source_lock['official_input']['place'], 'ORIGINAL_PLACE')
    require(not args.out.exists() and not args.build_dir.exists(), 'NEW_OUTPUT_AND_BUILD_REQUIRED')
    args.out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    try:
        binary, built, toolchain_tree = frozen.build_repl(args.luau_source, args.build_dir, args.out, old,
            args.cmake, args.ninja, args.git, args.cc, args.cxx)
        pin = built['binary_before_suites']
        suites = {}
        for label, root in inputs.items():
            sources = root / 'sources'
            for old_name, spec in old['suites'].items():
                program, ranges, bodies = frozen.assemble(sources, old, old_name)
                name = label + '_legacy_' + old_name
                expected = {'exit': 0, 'cases': [[case, 'PASS'] for case in spec['expected_case_names']]}
                suites[name] = run_fixed(name, program, ranges, bodies, binary, pin, sources, expected, args.out, frozen, old, before[label])
            for variant in contract['server_profiles'][label]:
                spec = contract['server_variants'][variant]
                program, ranges, bodies = server_program(frozen, old, sections, helpers, sources, variant,
                    spec.get('extra_modules', []), spec.get('extra_engine', []), spec.get('case_section', 'SERVER_CASES'))
                name = label + '_server_' + variant
                suites[name] = run_fixed(name, program, ranges, bodies, binary, pin, sources,
                    spec['positive' if label == 'ON' else 'negative'], args.out, frozen, old, before[label])
            program, ranges, bodies = ui_program(frozen, old, sections, helpers, args.baseline_root / 'sources', sources)
            name = label + '_ui_full31'
            suites[name] = run_fixed(name, program, ranges, bodies, binary, pin, sources,
                contract['ui']['positive' if label == 'ON' else 'negative'], args.out, frozen, old, before[label])
        compile_command = frozen.command_log([args.cmake, '--build', args.build_dir, '--target', 'Luau.Compile.CLI', '--parallel', '2'],
                                              args.out, 'compile_build', 900)
        compiler = args.build_dir / 'luau-compile'
        compiler_pin = identity(read(compiler))
        require(b'Linking CXX executable luau-compile' in read(args.out / 'compile_build.stdout.log'), 'FRESH_COMPILER_REQUIRED')
        rojo_pin = identity(read(args.rojo))
        require(rojo_pin == contract['rojo_binary'], 'PINNED_ROJO_BINARY')
        places, compilation = {}, {}
        for label, root in inputs.items():
            compile_rows = []
            for relative in sorted(before[label]):
                result = subprocess.run([str(compiler), '--text', str(root / 'sources' / relative)],
                    env=frozen.clean_environment(), capture_output=True, timeout=60)
                require(result.returncode == 0 and result.stderr == b'', 'COMPILE_FAILED:' + label + ':' + relative)
                compile_rows.append({'path': relative, 'source': before[label][relative], 'exit': 0, 'stdout': identity(result.stdout)})
            compilation[label] = compile_rows
            place = args.out / ('GQ470_S1A_' + label + '_PRIVATE.rbxlx')
            frozen.command_log([args.rojo, 'build', root / apply_source.PROJECT, '-o', place], args.out, 'rojo_' + label, 60)
            places[label] = verify_place(place, args.baseline_root / 'EGGRUMBLE_REAL69_PRIVATE.rbxlx', root / 'sources', args.baseline_root / 'sources')
            if label != 'ON':
                require(identity(read(place)) == source_lock['official_input']['place'], 'OFF_H93_PLACE_NOT_BYTE_EXACT')
            require(frozen.source_snapshot(root / 'sources') == before[label], 'FINAL_SOURCE_MUTATION')
        require(identity(read(binary)) == pin and identity(read(compiler)) == compiler_pin
                and identity(read(args.rojo)) == rojo_pin, 'EXECUTABLE_MUTATION')
        require(frozen.verify_clean_source(args.luau_source, args.git, old['toolchain']) == toolchain_tree, 'TOOLCHAIN_MUTATION')
        for tool in built['tools'].values():
            require(identity(read(Path(tool['path']))) == {k: tool[k] for k in ('bytes', 'sha256')}, 'BUILD_TOOL_MUTATION')
        for label, root in inputs.items():
            require(frozen.source_snapshot(root / 'sources') == before[label], 'FINAL_ENTIRE69_PROFILE:' + label)
            require(identity(read(root / apply_source.PROJECT)) == {k: source_lock['project'][k] for k in ('bytes', 'sha256')}, 'FINAL_PROJECT:' + label)
        require(identity(read(args.artifact_zip)) == source_lock['official_input']['zip'], 'FINAL_OFFICIAL_ZIP')
        require(identity(read(args.baseline_root / 'EGGRUMBLE_REAL69_PRIVATE.rbxlx')) == source_lock['official_input']['place'], 'FINAL_OFFICIAL_PLACE')
        frozen.fixture_snapshot(old)
        load_inputs()
        require(repository_snapshot(frozen, args.git, args.head, contract) == repository_before, 'REPO_CHANGED_DURING_GATE')
        built['binary_after_suites'] = pin
        built['execution_context'] = {'source_candidate_head': args.head, 'formal_rc': apply_source.BASE_RC, 'candidate_only': True}
        write_json(args.out / 'build_receipt.json', built)
        write_json(args.out / 'compile_receipt.json', {'compiler': compiler_pin, 'build': compile_command, 'profiles': compilation})
        receipt = {
            'schema': 'GQ470_P0D033_S1A_FIXED_GATE_V1', 'status': 'PASS_SOURCE_NATIVE_ROJO_ONLY',
            'started_at_utc': started, 'completed_at_utc': datetime.now(timezone.utc).isoformat(),
            'source_candidate_head': args.head, 'formal_rc': apply_source.BASE_RC,
            'source_count_pinned': 69, 'changed_sources': 4, 'unchanged_sources': 65,
            'input_lock': identity(read(HERE / 'INPUT_LOCK.json')), 'runner': identity(read(Path(__file__))),
            'build_receipt': identity(read(args.out / 'build_receipt.json')), 'compile_receipt': identity(read(args.out / 'compile_receipt.json')),
            'suites': suites, 'places': places, 'inverse_source_and_place_exact': True,
            'source_profiles': before, 'source_inputs_unchanged': True,
            'repository_files_bound_to_head': repository_before,
            'server_execution_matrix': contract['server_profiles'],
            'original_contracts_modified': False, 'new_candidate_contract': True,
            'active_runtime': 'rich51', 'private_companion': 'REAL69_UNION22', 'runtime_unified': False,
            'PREP_READY': False, 'rc_write_authorized': False, 'formal_rc_adoption': False,
            'persistent_growth_wired': False, 'full_S1_complete': False,
            'studio': 'NOT_TESTED', 'android': 'NOT_TESTED', 'art': 'ART_NO_GO', 'fun': 'NOT_TESTED',
            'limitations': contract['limitations'],
        }
        write_json(args.out / 'receipt.json', receipt)
        print(receipt['status'], flush=True)
    except Exception as error:
        write_json(args.out / 'FAILED.json', {'schema': 'GQ470_S1A_FAILED_GATE_V1', 'status': 'FAIL_NO_ADMISSION',
                   'source_candidate_head': args.head, 'reason': str(error)})
        raise


if __name__ == '__main__':
    main()
