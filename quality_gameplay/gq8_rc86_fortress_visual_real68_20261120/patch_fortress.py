#!/usr/bin/env python3
"""Non-destructive partial legacy RC86 FB015 castle detail port to the existing V3 art owner.

No extra Luau node, Game/Combat/Store/Remote, collision or paid policy.
NOT a claim of full RC85/86 48-flag semantic parity or Studio/Android success.
"""
import argparse
import hashlib
import json
import pathlib
import shutil

TARGET = "ServerScriptService/EGGRUMBLE_FlagshipFieldArt"
EXPECTED = "91c89619b2d4819cde31a8f63865fb6b73fee6c0e5b2d30564383f0fd1fa458b"
MARKER = "GQ8_RC86_FB015_FORTRESS_DETAIL_VISUAL_PORT_REAL68_20261120"


def digest(b):
    return hashlib.sha256(b).hexdigest()


def files(project, root):
    found = {}
    def walk(node, parts=()):
        if '$path' in node:
            route = '/'.join(parts)
            assert route not in found, route
            f = (root / node['$path']).resolve()
            assert f.is_relative_to(root.resolve()) and f.is_file(), route
            found[route] = (f, f.read_bytes(), node.get('$className'))
        else:
            for k, child in node.items():
                if not k.startswith('$') and isinstance(child, dict):
                    walk(child, parts + (k,))
    walk(project['tree'])
    return found


def patch(source):
    assert MARKER not in source, 'DUPLICATE_FORTRESS_PORT'
    assert source.count('local MAX_CASTLE_PARTS = 11') == 1
    source = source.replace('local MAX_CASTLE_PARTS = 11', 'local MAX_CASTLE_PARTS = 19')
    anchor = ''' local finial=add("TowerFinial","Wedge",Vector3.new(2.8,2.6,2.8),
  Vector3.new(26,23.1,-26),bronze,Enum.Material.Metal)
'''
    assert source.count(anchor) == 1, 'CASTLE_ANCHOR_MOVED'
    extra = ''' -- GQ8_RC86_FB015_FORTRESS_DETAIL_VISUAL_PORT_REAL68_20261120
 -- Original RC86 FB015_FORTRESS_DETAIL_ART_V2 roof/slit/banner motif is
 -- selectively adapted to this *existing* V3 castle owner, not the old S1 Game.
 -- Eight static lightweight art parts/castle. No Core/Gate/HP/egg interaction.
 for _,x in ipairs({-16,-5,5,16}) do
  add("FB015Slit"..tostring(x),"Block",Vector3.new(1.1,4.0,.35),
   Vector3.new(x,13.4,-14.5),darkStone,Enum.Material.Slate)
 end
 for _,x in ipairs({-20,20}) do
  add("FB015Banner"..tostring(x),"Wedge",Vector3.new(3.1,6.2,.3),
   Vector3.new(x,13.6,-14.8),teamTrim,Enum.Material.Fabric)
 end
 for _,x in ipairs({-25,25}) do
  add("FB015RoofFinial"..tostring(x),"Cylinder",Vector3.new(1.7,3.4,1.7),
   Vector3.new(x,25.4,-26),bronze,Enum.Material.Metal)
 end
 deco:SetAttribute("LegacyRC86FortressDetail", "SELECTIVE_VISUAL_PORT_ONLY")
'''
    source = source.replace(anchor, anchor + extra)
    assert source.count(MARKER) == 1
    assert source.count('local MAX_CASTLE_PARTS = 19') == 1
    assert source.count('CanCollide=false') >= 1 and source.count('CanQuery=false') >= 1
    return source


def run(root, head):
    project_path = root / 'EGGRUMBLE_REAL68.project.json'
    receipt_path = root / 'REAL68_LEGACY_INTAKE_RECEIPT.json'
    project = json.loads(project_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    before = files(project, root)
    assert len(before) == 68 and TARGET in before
    assert receipt['selected_source_count'] == 68 and len(receipt['source_hashes']) == 68
    assert receipt['candidate_head'] == head
    assert digest(before[TARGET][1]) == EXPECTED, 'TARGET_ORIGINAL_SOURCE_MISMATCH'
    assert not (root / 'off68_fortress').exists(), 'NO_DOUBLE_ROLLBACK'
    for route, (_, raw, _) in before.items():
        assert receipt['source_hashes'][route] == digest(raw), 'PARENT_DIGEST_' + route
    previous = root / 'off68_fortress'
    previous.mkdir()
    for f, raw, _ in before.values():
        dest = previous / f.relative_to(root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
    (previous / project_path.name).write_bytes(project_path.read_bytes())
    shutil.copyfile(root / 'EGGRUMBLE_REAL68_PRIVATE.rbxlx',
                    root / 'OFF68_PRE_FORTRESS_EXACT.rbxlx')
    old_source = before[TARGET][1].decode('utf-8')
    new_source = patch(old_source).encode('utf-8')
    before[TARGET][0].write_bytes(new_source)
    after = files(project, root)
    rollback = files(project, previous)
    assert len(after) == len(rollback) == 68 and set(after) == set(rollback)
    for route, (_, raw, cls) in before.items():
        assert rollback[route][1] == raw and rollback[route][2] == cls, route
        assert after[route][1] == (new_source if route == TARGET else raw), route
        assert after[route][2] == cls, route
    receipt['source_hashes'][TARGET] = digest(new_source)
    receipt['rc86_fortress_detail_visual'] = {
        'original_legacy_flag': 'FB015_FORTRESS_DETAIL_ART_V2',
        'original_rc86_artifact': 14161823401,
        'port_marker': MARKER,
        'single_existing_owner': TARGET,
        'original_68_routes_preserved': True,
        'only_existing_art_source_modified': True,
        'pre_art_exact_rollback': 'off68_fortress plus OFF68_PRE_FORTRESS_EXACT.rbxlx',
        'visual_details_per_castle': 8,
        'gameplay_semantic_parity': 'NOT_PROVEN',
        'studio': 'NOT_TESTED',
        'android_15min': 'NOT_TESTED',
        'product_acceptance': 'NO_GO',
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    print('RC86_FB015_FORTRESS_SELECTIVE_REAL68_SOURCE_PORT_OFF68_PASS', len(after))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--base', type=pathlib.Path, required=True)
    p.add_argument('--head', required=True)
    a = p.parse_args()
    run(a.base, a.head)
