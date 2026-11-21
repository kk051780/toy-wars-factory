#!/usr/bin/env python3
"""GQ470: source-locked REAL69 pickup ornament visibility, A-only visual fix.

Consumes the *actual* official Actions ZIP, not a guessed Studio project. No
privileged game, inventory or score source is modified. This is not a formal RC
writer or an Android/ART acceptance test.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

OFFICIAL_HEAD = 'e80973c354f14a0d0088577f3cc1a875454f0f8f'
TARGET = 'ServerScriptService/EGGRUMBLE_EncounterReadabilityArt'
TARGET_FILE = 'sources/ServerScriptService/EGGRUMBLE_EncounterReadabilityArt.server.luau'
TARGET_SHA = '9ec9982ed0d6e68457712e4e5dd10e7fb608c666adfe2e6904a209f5692a50c9'
FEATURE = 'GQ470_FB015_PICKUP_ORNAMENT_VISIBILITY_REAL69_20261122'
START = 'local function decorateFieldItem(item:BasePart)\n'
END = '\nlocal function decorateVault(part:BasePart)'
OLD_END = ''' item.Destroying:Connect(function()
  activeItems[world]=math.max(0,(activeItems[world] or 1)-1)
  marked[item]=nil
 end)
end
'''
NEW_END = ''' -- GQ470_FB015_PICKUP_ORNAMENT_VISIBILITY_REAL69_20261122
 -- The original Item engine hides the real pickup on consume and restores it
 -- on respawn. Keep our TWO existing matte ornaments in the same visibility
 -- state, including an item decorated while its spawn is already inactive.
 -- This is signal-driven (zero extra Part, UI, polling loop, or Remote).
 local function syncItemArtVisibility()
  if not item.Parent or not trim.Parent then return end
  local alpha=if item.Transparency>=.99 or not item.CanQuery then 1 else item.Transparency
  for _,child in ipairs(trim:GetChildren()) do
   if child:IsA("BasePart") and math.abs(child.Transparency-alpha)>.001 then
    child.Transparency=alpha
   end
  end
 end
 local transparencyConnection=item:GetPropertyChangedSignal("Transparency"):Connect(syncItemArtVisibility)
 local queryConnection=item:GetPropertyChangedSignal("CanQuery"):Connect(syncItemArtVisibility)
 syncItemArtVisibility()
 item.Destroying:Connect(function()
  transparencyConnection:Disconnect()
  queryConnection:Disconnect()
  activeItems[world]=math.max(0,(activeItems[world] or 1)-1)
  marked[item]=nil
 end)
end
'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def walk_project(node: dict, route: str = '') -> dict[str, str]:
    found = {}
    if '$path' in node:
        found[route] = node['$path']
    for k, value in node.items():
        if not k.startswith('$') and isinstance(value, dict):
            child_route = f'{route}/{k}' if route else k
            found.update(walk_project(value, child_route))
    return found


def transform(source: str) -> str:
    if FEATURE in source:
        raise ValueError('RED_DOUBLE_APPLY')
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError('RED_ITEM_BOUNDARY')
    before, rest = source.split(START, 1)
    item_block, after = rest.split(END, 1)
    if item_block.count(OLD_END) != 1 or not item_block.endswith(OLD_END):
        raise ValueError('RED_ITEM_END_ANCHOR')
    required = (
        'if marked[item] then return end',
        'if kind~="HEAL" and kind~="DASH" and kind~="SHIELD" then return end',
        'MAX_DECORATED_ITEMS_PER_WORLD',
        'trim.Name="EGGRUMBLE_FieldItemVisual_VisualOnly"',
        'trim.Parent=item',
        'jewel(trim,item,"GroundHalo"',
        'jewel(trim,item,"RemedyCross"',
        'jewel(trim,item,"WingTip"',
        'jewel(trim,item,"GuardDiamond"',
    )
    if any(r not in item_block for r in required):
        raise ValueError('RED_ORIGINAL_VISUAL_CONTRACT')
    if item_block.count('jewel(trim,item,') != 4:
        raise ValueError('RED_ORNAMENT_BUDGET')
    if 'if not RunService:IsStudio() then return end' not in before:
        raise ValueError('RED_STUDIO_ONLY')
    if not all(s in source for s in ('p.CanCollide=false', 'p.CanTouch=false', 'p.CanQuery=false')):
        raise ValueError('RED_NO_GAME_PHYSICS')
    out = before + START + item_block.replace(OLD_END, NEW_END, 1) + END + after
    if out.count(FEATURE) != 1:
        raise ValueError('RED_PATCH_MARKER')
    if before != out.split(START, 1)[0] or after != out.split(END, 1)[1]:
        raise ValueError('RED_OTHER_OWNER_CHANGE')
    if out.count('jewel(trim,item,') != source.count('jewel(trim,item,'):
        raise ValueError('RED_NEW_VISUAL_OBJECT')
    return out


def patch_artifact(artifact: Path, out: Path) -> dict:
    with zipfile.ZipFile(artifact) as z:
        names = set(z.namelist())
        receipt = json.loads(z.read('REAL69_LEGACY_INTAKE_RECEIPT.json'))
        project = json.loads(z.read('EGGRUMBLE_REAL69.project.json'))
        mapping = walk_project(project['tree'])
        hashes = receipt['source_hashes']
        if receipt.get('build_head') != OFFICIAL_HEAD or receipt.get('canonical_build') is not True:
            raise ValueError('RED_OFFICIAL_HEAD')
        if len(mapping) != 69 or set(mapping) != set(hashes) or len(hashes) != 69:
            raise ValueError('RED_SOURCE69_ROUTE_SET')
        if receipt.get('source_hashes', {}).get(TARGET) != TARGET_SHA:
            raise ValueError('RED_TARGET_SHA_RECEIPT')
        for route, path in mapping.items():
            if path not in names or not path.startswith('sources/') or '..' in Path(path).parts:
                raise ValueError('RED_SOURCE_PATH')
            if sha(z.read(path)) != hashes[route]:
                raise ValueError('RED_SOURCE_HASH:' + route)
        if mapping[TARGET] != TARGET_FILE:
            raise ValueError('RED_TARGET_ROUTE')
        original = z.read(TARGET_FILE)
        if sha(original) != TARGET_SHA:
            raise ValueError('RED_ORIGINAL_SHA')
        changed = transform(original.decode('utf-8')).encode('utf-8')
        out.mkdir(parents=True, exist_ok=True)
        for route, path in mapping.items():
            fp = out / path
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(changed if route == TARGET else z.read(path))
        for filename in ('EGGRUMBLE_REAL69.project.json', 'EGGRUMBLE_REAL69_PRIVATE.rbxlx'):
            (out / filename).write_bytes(z.read(filename))
        off_root = out / 'OFF69_original'
        (off_root / TARGET_FILE).parent.mkdir(parents=True, exist_ok=True)
        (off_root / TARGET_FILE).write_bytes(original)
        (off_root / 'EGGRUMBLE_REAL69_PRIVATE.rbxlx').write_bytes(z.read('EGGRUMBLE_REAL69_PRIVATE.rbxlx'))
        receipt['source_hashes'][TARGET] = sha(changed)
        receipt['gq470_item_ornament_visibility'] = {
            'feature_id': FEATURE,
            'official_head': OFFICIAL_HEAD,
            'only_changed_route': TARGET,
            'unchanged_selected_sources': 68,
            'ornament_parts_per_item_before_after': [2, 2],
            'zero_extra_loop': True,
            'extra_signals_per_item': 2,
            'original_item_game_authority_modified': False,
            'studio_actual_patch_retest': 'NOT_TESTED',
            'android_15min': 'NOT_TESTED',
            'art_owner_acceptance': False,
            'formal_rc_integrated': False,
        }
        (out / 'REAL69_LEGACY_INTAKE_RECEIPT.json').write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
        for route, path in mapping.items():
            body = (out / path).read_bytes()
            if sha(body) != receipt['source_hashes'][route]:
                raise ValueError('RED_OUTPUT_SOURCE_LOCK:' + route)
        if (out / 'OFF69_original/EGGRUMBLE_REAL69_PRIVATE.rbxlx').read_bytes() != z.read('EGGRUMBLE_REAL69_PRIVATE.rbxlx'):
            raise ValueError('RED_OFF_PLACE_BYTES')
        return {'feature_id': FEATURE, 'official_head': OFFICIAL_HEAD, 'original_sha256': sha(original),
                'patched_sha256': sha(changed), 'original_bytes': len(original), 'patched_bytes': len(changed),
                'unchanged_sources': 68, 'original_private_place_bytes': len(z.read('EGGRUMBLE_REAL69_PRIVATE.rbxlx')),
                'private_place_is_unmodified_original': True, 'studio_tested': False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--artifact', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(patch_artifact(args.artifact, args.output), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
