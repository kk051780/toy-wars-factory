#!/usr/bin/env python3
"""Source-locked, reversible REAL69 objective art repair (visual only)."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE = 'c226c63eeb235503f9292503b61f2173550337ec'
TARGET = 'ServerScriptService/EGGRUMBLE_EncounterReadabilityArt'
PROJECT = 'EGGRUMBLE_REAL69.project.json'
RECEIPT = 'REAL69_LEGACY_INTAKE_RECEIPT.json'
EXPECTED_SHA = '899cc3a1fddcf53b31a163f7e406f3758e1b607b185fc1d1f27ce10952d1be97'
FEATURE = 'GQ470_P0_FIELD_RELEASED_EGG_CREST_REAL69_20261120'
OLD_EGG = ''' jewel(trim,egg,"GoldenCradle","Cylinder",Vector3.new(.16,4.35,4.35),
  CFrame.new(0,-1.5,0)*CFrame.Angles(0,0,math.rad(90)),gold,Enum.Material.Metal)
 jewel(trim,egg,"TopGem","Wedge",Vector3.new(1.1,.85,1.1),
  CFrame.new(0,1.54,0),jade,Enum.Material.Glass,.12)
'''
NEW_EGG = ''' -- GQ470_P0_FIELD_RELEASED_EGG_CREST_REAL69_20261120
 -- Keep two ornament Parts per egg (56 pieces max in 28-egg arena), no on-screen UI.
 -- Released eggs have a warm accent to distinguish the post-castle-loot phase.
 local isReleased = egg.Name:match("^ReleasedEgg_") ~= nil
 local crestTint = if isReleased then maroon else jade
 jewel(trim,egg,"ObjectiveBaseRing","Cylinder",Vector3.new(.16,5.0,5.0),
  CFrame.new(0,-1.5,0)*CFrame.Angles(0,0,math.rad(90)),gold,Enum.Material.Metal)
 jewel(trim,egg,"RaisedEggCrest","Wedge",Vector3.new(1.9,2.2,1.35),
  CFrame.new(0,1.85,0)*CFrame.Angles(0,math.rad(45),0),crestTint,Enum.Material.SmoothPlastic)
'''
def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def selected(root: Path) -> dict[str, Path]:
    project = json.loads((root / PROJECT).read_text())
    output: dict[str, Path] = {}
    def walk(node, route=''):
        if not isinstance(node, dict):
            return
        if '$path' in node:
            p = (root / node['$path']).resolve()
            assert p.is_relative_to(root.resolve()) and p.is_file(), 'RED_PROJECT_PATH'
            assert route not in output, 'RED_DUPLICATE_ROUTE'
            output[route] = p
        for k, child in node.items():
            if not k.startswith('$'):
                walk(child, route + '/' + k if route else k)
    walk(project['tree'])
    return output


def transform(source: str) -> str:
    assert FEATURE not in source, 'RED_DOUBLE_APPLY'
    assert source.count(OLD_EGG) == 1, 'RED_EGG_ANCHOR'
    assert 'if not RunService:IsStudio() then return end' in source, 'RED_STUDIO_FENCE'
    assert 'MAX_DECORATED_EGGS_PER_ARENA=28' in source, 'RED_EGG_BUDGET'
    assert 'p.CanCollide=false' in source and 'p.CanTouch=false' in source and 'p.CanQuery=false' in source, 'RED_VISUAL_PHYSICS'
    assert 'local function decorateEgg(egg:BasePart)' in source and 'local function decorateVault(part:BasePart)' in source, 'RED_OWNERS'
    out = source.replace(OLD_EGG, NEW_EGG, 1)
    assert out.count(FEATURE) == 1, 'RED_PATCH_MARKER'
    assert source.split('local function decorateVault(part:BasePart)',1)[1] == out.split('local function decorateVault(part:BasePart)',1)[1], 'RED_STATION_OWNER_OVERLAP'
    assert 'BillboardGui' not in NEW_EGG, 'RED_GUI'
    assert NEW_EGG.count('jewel(') == 2, 'RED_EGG_PART_BUDGET'
    return out


def self_test():
    source = '''if not RunService:IsStudio() then return end
MAX_DECORATED_EGGS_PER_ARENA=28
p.CanCollide=false
p.CanTouch=false
p.CanQuery=false
local function decorateEgg(egg:BasePart) end
''' + OLD_EGG + 'local function decorateVault(part:BasePart) end\n'
    candidate = transform(source)
    assert 'isReleased' in candidate and 'RaisedEggCrest' in candidate
    for bad in [candidate, source.replace(OLD_EGG,''), source.replace('local function decorateEgg(egg:BasePart)','local function decorateNoEgg(egg:BasePart)'),
                source.replace('p.CanCollide=false','p.CanCollide=true'),
                source.replace('if not RunService:IsStudio() then return end', '')]:
        try:
            transform(bad)
        except AssertionError:
            continue
        raise AssertionError('RED_MUTANT_ACCEPTED')
    print('P0_OBJECTIVE_ART_SELFTEST_5_NEGATIVES_PASS')


def main(root: Path):
    paths = selected(root)
    receipt_file = root / RECEIPT
    receipt = json.loads(receipt_file.read_text())
    assert len(paths) == 69 and len(receipt['source_hashes']) == 69, 'RED_69_SOURCE_COUNT'
    assert receipt.get('build_head') == BASE and receipt.get('canonical_build') is True, 'RED_STALE_BASE'
    assert receipt.get('source_hashes', {}).get(TARGET) == EXPECTED_SHA, 'RED_TARGET_RECEIPT'
    for route, path in paths.items():
        assert digest(path.read_bytes()) == receipt['source_hashes'][route], 'RED_SOURCE_HASH_'+route
    original = paths[TARGET].read_bytes()
    assert digest(original) == EXPECTED_SHA, 'RED_TARGET_BYTES'
    modified = transform(original.decode('utf-8')).encode('utf-8')
    assert modified != original
    undo = root/'off69_objective'
    assert not undo.exists(), 'RED_ALREADY_PATCHED'
    undo.mkdir()
    shutil.copy2(root/PROJECT,undo/PROJECT)
    shutil.copy2(receipt_file,undo/RECEIPT)
    shutil.copy2(root/'EGGRUMBLE_REAL69_PRIVATE.rbxlx',undo/'EGGRUMBLE_REAL69_PRIVATE.rbxlx')
    shutil.copytree(root/'sources',undo/'sources')
    paths[TARGET].write_bytes(modified)
    changed = {route for route, path in paths.items() if path.read_bytes() != selected(undo)[route].read_bytes()}
    assert changed == {TARGET}, 'RED_NONOVERLAP'
    receipt['source_hashes'][TARGET] = digest(modified)
    receipt['gq470_objective_visual'] = {
        'feature_id': FEATURE, 'official_base': BASE,
        'only_changed_selected_route': TARGET,
        'other_selected_routes_byte_exact': 68,
        'decorative_egg_parts_per_egg_old_new': [2,2],
        'vault_deposit_source_untouched': True,
        'scope_nonoverlap_with_pr_922': 'decorateEgg_only',
        'additional_vault_parts_per_station': 0,
        'collision_changed': False, 'authority_changed': False,
        'reversible_off': 'off69_objective',
        'visual_evidence': 'NOT_TESTED', 'android_15min': 'NOT_TESTED',
        'owner_accepted': False
    }
    receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    assert selected(root).keys() == selected(undo).keys()
    print('P0_OBJECTIVE_ART_REAL69_SOURCE_PATCH_READY', digest(modified))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        assert args.base is not None, 'RED_MISSING_BASE'
        main(args.base)
