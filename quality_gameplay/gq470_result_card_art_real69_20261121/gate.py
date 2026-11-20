#!/usr/bin/env python3
"""Source-exact REAL69 result card ART patch (A candidate, not official RC)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
PATCH = HERE / 'RESULT_MATTE_REAL69.patch'
OFFICIAL = 'e80973c354f14a0d0088577f3cc1a875454f0f8f'
RUN = 44695199140
ARTIFACT = 14610422120
FEATURE = 'GQ470_FB015_MATTE_RESULT_CARD_REAL69_20261121'
ROUTE = 'ServerScriptService/EGGRUMBLE_MatchResultService'
RELATIVE = 'sources/ServerScriptService/EGGRUMBLE_MatchResultService.luau'
PROJECT = 'EGGRUMBLE_REAL69.project.json'
RECEIPT = 'REAL69_LEGACY_INTAKE_RECEIPT.json'
ORIGINAL_SHA = '5fbb6a5017363bb8ef2a9793e279a1cb8a76480f6b2e74758ec35188508ce1a4'
NEW_SHA = '2870337b83979f7981739accc91cbcb12deea5fe3cd7c2ab77ebea8781b77cec'


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError('RED_GQ470_RESULT_ART_' + reason)


def selected(root: Path) -> dict[str, Path]:
    tree = json.loads((root / PROJECT).read_text(encoding='utf8'))['tree']
    paths: dict[str, Path] = {}
    def visit(node: dict, segments: list[str]):
        for name, item in node.items():
            if name.startswith('$') or not isinstance(item, dict):
                continue
            parts = segments + [name]
            route = '/'.join(parts)
            if '$path' in item:
                path = (root / item['$path']).resolve()
                require(path.is_relative_to(root.resolve()), 'PROJECT_TRAVERSAL')
                require(path.is_file() and route not in paths, 'DUPLICATE_OR_MISSING_ROUTE')
                paths[route] = path
            else:
                visit(item, parts)
    visit(tree, [])
    require(len(paths) == 69 and paths.get(ROUTE) == root / RELATIVE,
            '69_SELECTED_TARGET_SOURCE')
    return paths


def validate_original(source: str) -> None:
    require(source.startswith('--!strict\n'), 'STRICT_SOURCE_REQUIRED')
    require(source.count('local function makeResultGui(') == 1,
            'SINGLE_RESULT_UI_OWNER')
    require(source.count('local function resultText(') == 1,
            'SINGLE_TRUE_SCORE_SOURCE')
    require('ResultRetry.MAX_RETRIES = 8' in source, 'RESULT_DELIVERY_PRESERVED')
    require('local DISPLAY_SECONDS=8' in source, 'EIGHT_SECONDS_PRESERVED')
    require('session.resultsDelivered=true' in source, 'ONE_RESULT_PER_MATCH')
    require('assert(RunService:IsStudio(),' in source, 'STUDIO_FENCE_PRESERVED')
    require('frame.Size=UDim2.new(.82,0,0,94)' in source,
            'MOBILE_HEIGHT_OR_WIDTH_DRIFT')
    require('constraint.MaxSize=Vector2.new(480,94)' in source
            and 'constraint.MinSize=Vector2.new(245,94)' in source,
            'MOBILE_BOUNDS_DRIFT')
    require('statsLabel.Text=stats:gsub(" 納","\\n納",1)' in source,
            'MOBILE_TWO_LINE_VERIFIED_RESULTS')
    require(source.count('Instance.new("ScreenGui")') == 1,
            'DUPLICATE_SCREEN_GUI')


def validate_patch(original: str, candidate: str) -> None:
    validate_original(original)
    validate_original(candidate)
    require(FEATURE not in original and candidate.count(FEATURE) == 1,
            'PROVENANCE_MARKER')
    require('frame.BackgroundColor3=Color3.fromRGB(23,34,48)' in original and
            'frame.BackgroundColor3=Color3.fromRGB(255,255,255)' in candidate,
            'GRADIENT_BASE_COLOR')
    for token in ('local matte=Instance.new("UIGradient")',
                  'local outline=Instance.new("UIStroke")',
                  'local rail=Instance.new("Frame")',
                  'rail.Size=UDim2.fromOffset(3,54)',
                  'outline.Thickness=1',
                  'outline.Transparency=.52',
                  'matte.Rotation=90',
                  'elseif title:find("引き分け",1,true)',
                  'if won then Color3.fromRGB(245,199,100)',
                  'rail.BackgroundColor3=accent'):
        require(token in candidate, 'VISUAL_CONTRACT_' + token)
    require(candidate.count('Instance.new(') - original.count('Instance.new(') == 3,
            'ONLY_THREE_STATIC_UI_INSTANCES')
    require(original.count('Instance.new("Part")') ==
            candidate.count('Instance.new("Part")'), 'NO_WORLD_PARTS')
    for forbidden in ('RenderStepped:Connect(', 'Heartbeat:Connect(',
                      'DataStoreService', ':FireServer(', 'MarketplaceService'):
        require(candidate.count(forbidden) == original.count(forbidden),
                'AUTHORITY_OR_RENDER_COST_' + forbidden)
    before_tail = original.split('local function makeResultGui(', 1)[1].split(
        '\nfunction ResultService.showIfFinished(', 1)[1]
    after_tail = candidate.split('local function makeResultGui(', 1)[1].split(
        '\nfunction ResultService.showIfFinished(', 1)[1]
    require(before_tail == after_tail, 'SESSION_AUTHORITY_SOURCE_CHANGED')
    require(original.split('local function makeResultGui(', 1)[0] ==
            candidate.split('local function makeResultGui(', 1)[0],
            'SCORE_OR_RETRY_SOURCE_CHANGED')
    # Exact diff application: no more or fewer changes than the committed patch.
    with_fixed_background = original.replace(
        'frame.BackgroundColor3=Color3.fromRGB(23,34,48)',
        'frame.BackgroundColor3=Color3.fromRGB(255,255,255)', 1)
    added = candidate.split(' corner.Parent=frame\n', 1)[1].split(
        ' local titleLabel=Instance.new("TextLabel")', 1)[0]
    require(added.count(FEATURE) == 1 and
            with_fixed_background.replace(' corner.Parent=frame\n\n',
                                          ' corner.Parent=frame\n'+added, 1) == candidate,
            'MODIFIED_ANYTHING_BEYOND_CARD_ART')


def negative_tests(original: str, candidate: str) -> int:
    variants = (
        candidate.replace('rail.Size=UDim2.fromOffset(3,54)',
                          'rail.Size=UDim2.fromOffset(300,54)', 1),
        candidate.replace('elseif title:find("引き分け",1,true)',
                          'elseif false', 1),
        candidate.replace('local DISPLAY_SECONDS=8',
                          'local DISPLAY_SECONDS=80', 1),
        candidate.replace('session.resultsDelivered=true',
                          'session.resultsDelivered=false', 1),
        candidate.replace('outline.Thickness=1', 'outline.Thickness=7', 1),
        candidate + '\nInstance.new("ScreenGui")\n',
        candidate.replace('statsLabel.Text=stats:gsub(" 納","\\n納",1)',
                          'statsLabel.Text="fake"', 1),
        candidate.replace(FEATURE, FEATURE + FEATURE, 1),
    )
    for i, mutant in enumerate(variants):
        try:
            validate_patch(original, mutant)
        except AssertionError:
            continue
        raise AssertionError('MUTANT_NOT_REJECTED_' + str(i))
    return len(variants)


def compose(base: Path, out: Path) -> dict:
    require(not out.exists(), 'NO_OVERWRITE_EXISTING')
    files = selected(base)
    receipt = json.loads((base / RECEIPT).read_text(encoding='utf8'))
    require(receipt.get('build_head') == OFFICIAL and
            receipt.get('selected_source_count') == 69 and
            len(receipt.get('source_hashes', {})) == 69,
            'OFFICIAL_RECEIPT_BASE')
    require(receipt['source_hashes'].get(ROUTE) == ORIGINAL_SHA and
            sha(files[ROUTE].read_bytes()) == ORIGINAL_SHA,
            'SOURCE_ORIGINAL_SHA')
    for route, file in files.items():
        require(sha(file.read_bytes()) == receipt['source_hashes'][route],
                'SOURCE_SHA_' + route)
    shutil.copytree(base, out)
    rollback = out / 'OFF69_SOURCE_EXACT'
    rollback.mkdir()
    shutil.copytree(base / 'sources', rollback / 'sources')
    shutil.copy2(base / PROJECT, rollback / PROJECT)
    shutil.copy2(base / RECEIPT, rollback / RECEIPT)
    try:
        subprocess.run(['patch', '-p1', '--fuzz=0', '--batch',
                        '-i', str(PATCH)], check=True, cwd=out,
                       capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise AssertionError('PATCH_COULD_NOT_APPLY_EXACTLY_' + e.stderr) from e
    on = selected(out)
    off = selected(rollback)
    require(set(on) == set(off) == set(files), 'ROUTE_LOSS')
    changed = [route for route in files
               if on[route].read_bytes() != off[route].read_bytes()]
    require(changed == [ROUTE], 'MORE_THAN_ONE_ROUTE_CHANGED')
    for route in files:
        require(files[route].read_bytes() == off[route].read_bytes(),
                'OFF_SOURCE_NOT_EXACT_' + route)
        if route != ROUTE:
            require(files[route].read_bytes() == on[route].read_bytes(),
                    'OTHER_68_SOURCES_DRIFTED_' + route)
    source0 = files[ROUTE].read_text(encoding='utf8')
    source1 = on[ROUTE].read_text(encoding='utf8')
    require(sha(source1.encode('utf8')) == NEW_SHA, 'NEW_SOURCE_PINNED_SHA')
    validate_patch(source0, source1)
    mutants = negative_tests(source0, source1)
    report = {
        'feature_id': FEATURE,
        'formal_rc_head_before_admission': OFFICIAL,
        'canonical_profile': 'REAL69_PRIVATE_COMPANION',
        'official_artifact_id': ARTIFACT,
        'official_source_run_id': RUN,
        'selected_source_count': 69,
        'unchanged_source_count': 68,
        'changed_selected_routes': changed,
        'target_class': 'ModuleScript',
        'original_source_sha256': ORIGINAL_SHA,
        'candidate_source_sha256': NEW_SHA,
        'source_bytes_before_after': [len(source0.encode()), len(source1.encode())],
        'screen_gui_delta': 0,
        'transient_ui_instance_delta': 3,
        'new_world_parts': 0,
        'new_render_connections': 0,
        'new_remotes': 0,
        'score_session_authority_changed': False,
        'negative_tests_rejected': mutants,
        'source_lock': 'one existing selected MatchResultService, other 68 byte-exact',
        'rollback': 'OFF69_SOURCE_EXACT preserves all 69 selected sources',
        'native_luau': 'PENDING_CI',
        'rojo_on_off': 'PENDING_CI',
        'studio_solo': 'NOT_TESTED',
        'studio_2client': 'NOT_TESTED',
        'android_15_min': 'NOT_TESTED',
        'before_after_images': '0/32',
        'art_gate': 'NO_GO',
        'fun_gate': 'NO_GO',
        'formal_rc_adopted': False,
        'owner_accepted': False,
    }
    receipt['source_hashes'][ROUTE] = NEW_SHA
    receipt['gq470_result_card_art_candidate'] = report
    (out / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    handoff = out / 'B220_ONE_SOURCE_NOT_FORMAL'
    (handoff / 'selected_sources').mkdir(parents=True)
    shutil.copy2(on[ROUTE], handoff / 'selected_sources/EGGRUMBLE_MatchResultService.luau')
    (handoff / 'SOURCE_SELECT_MANIFEST.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    (out / 'ART_CHECK_REPORT_RESULT_CARD.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('GQ470_RESULT_MATTE_69_SOURCE_ONE_CHANGED_OFF69_NEG8_SOURCE_ONLY_PASS')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    compose(args.base.resolve(), args.out.resolve())


if __name__ == '__main__':
    main()
