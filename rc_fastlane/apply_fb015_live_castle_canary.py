#!/usr/bin/env python3
"""P0D #431 opt-in private non-Studio castle *source* canary.

Default/non-authorized live stays disabled; Studio preserves full author art.
Only the 36 large V3 gate ornaments are generated when an authorized private
test Place has Workspace attribute P0D_PRIVATE_LIVE_CASTLE=true before startup.
No public publish is authorized, no claims of runtime or beauty acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from apply_fb015_castle_gate_silhouette import (
    TARGET, FEATURE as CASTLE_V3, blob, read, patch as author_patch
)

FEATURE = "P0D_PRIVATE_LIVE_CASTLE_CANARY_V1"
ATTR = "P0D_PRIVATE_LIVE_CASTLE"
AUTHOR = Path(__file__).parent/"features/p0_playable_art77/CastleDetailArt.server.luau"

def expected_original() -> bytes:
    return author_patch(AUTHOR.read_bytes())

def one(source: str, old: str, new: str) -> str:
    assert source.count(old) == 1, ("PINNED_CASTLE_ANCHOR_DRIFT", old[:90], source.count(old))
    return source.replace(old, new, 1)

def patch(source: bytes) -> bytes:
    assert blob(source) == blob(expected_original()), "V3_AUTHOR_SOURCE_BLOB_DRIFT"
    s = source.decode("utf8")
    assert FEATURE not in s and "P0D_PRIVATE_LIVE_CASTLE" not in s
    assert s.count('if not RunService:IsStudio() then return end') == 1
    assert s.count('    -- FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3:') == 1
    assert s.count('    -- Gold/stone badges face the field; avoids giant world Billboard labels.') == 1
    assert s.count('teamCastle(-1,"RED",C(235,103,92))') == 1
    assert s.count('teamCastle(1,"BLUE",C(95,161,232))') == 1
    start = s.index('    -- FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3:')
    end = s.index('    -- Gold/stone badges face the field; avoids giant world Billboard labels.')
    v3 = s[start:end]
    assert 'V3_GATE_MERLON_COPING_' in v3 and 'V3_TEAM_COLOR_STANDARD_' in v3
    assert 'Instance.new("PointLight")' not in v3
    assert 'CanCollide = true' not in v3 and 'CanQuery = true' not in v3
    replacement = (
        '-- ' + FEATURE + ': PRIVATE TEST PLACE ONLY; no auto-live.\n'
        'local isStudioPreview = RunService:IsStudio()\n'
        'if not isStudioPreview and workspace:GetAttribute("' + ATTR + '") ~= true then return end'
    )
    s = one(s,'if not RunService:IsStudio() then return end',replacement)
    old = 'teamCastle(-1,"RED",C(235,103,92))\nteamCastle(1,"BLUE",C(95,161,232))'
    live = (
        'if isStudioPreview then\n'
        '    teamCastle(-1,"RED",C(235,103,92))\n'
        '    teamCastle(1,"BLUE",C(95,161,232))\n'
        'else\n'
        '    -- Non-Studio opt-in: 36 large visual-only parts; no tiny windows, roofs or lights.\n'
        '    local function liveGate(side: number, name: string, theme: Color3)\n'
        '        local art = Instance.new("Folder")\n'
        '        art.Name = name.."_PRIVATE_LIVE_GATE_CANARY"\n'
        '        art.Parent = folder\n'
        '        local gateX = side*84.3\n'
        '        local startCount = made\n'
        + v3 +
        '        assert(made-startCount==18,"LIVE_GATE_PARTS_NOT_18")\n'
        '        art:SetAttribute("LIVE_CANARY_ONLY",true)\n'
        '    end\n'
        '    liveGate(-1,"RED",C(235,103,92))\n'
        '    liveGate(1,"BLUE",C(95,161,232))\n'
        '    assert(made==36,"LIVE_GATE_PART_BUDGET_DRIFT")\n'
        'end\n'
        'folder:SetAttribute("StudioFullAuthorArt",isStudioPreview)\n'
        'folder:SetAttribute("PrivateLivePilot",not isStudioPreview)\n'
        'folder:SetAttribute("LiveArtOwnerAccepted",false)'
    )
    s = one(s,old,live)
    assert s.count('if not RunService:IsStudio() then return end') == 0
    assert s.count('workspace:GetAttribute("' + ATTR + '") ~= true') == 1
    assert s.count("assert(made==36,") == 1
    # Keep all game/HUD/server damage authority outside art module.
    for token in ('FireServer(', 'OnServerEvent:Connect(', 'TakeDamage(',
                  'GetDataStore(', 'MarketplaceService', 'CanCollide = true',
                  'CanQuery = true', 'Instance.new("ScreenGui")'):
        assert token not in s, ("UNSAFE_CASTLE_LIVE_SOURCE", token)
    return s.encode("utf8")

def apply(base: Path, out: Path, enabled: bool) -> bool:
    if not enabled:
        assert not out.exists(), "OFF_ZERO_WRITES"
        print("PRIVATE_LIVE_CASTLE_OFF_ZERO_WRITES")
        return False
    base = base.resolve()
    out = out.absolute()
    assert base.is_dir() and not base.is_symlink()
    assert out.parent.is_dir() and not out.parent.is_symlink() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before = read(base)
    assert len(before) == 80 and TARGET in before
    prev = {p:blob(data) for p,data in sorted(before.items())}
    assert prev[TARGET] == blob(expected_original()), "REQUIRES_CORRECT_V3_AUTHOR_BASE"
    sl = json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl = json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"] == fl["total_sources"] == 80
    assert sl["blobs"] == fl["source_gitblobs"] == prev, "LOCK_DRIFT_BEFORE"
    assert fl["feature_flags"].get(CASTLE_V3) is True, "MISSING_CASTLE_V3"
    assert not fl["feature_flags"].get(FEATURE,False), "DOUBLE_CANARY_ADOPTION"
    after = dict(before)
    after[TARGET] = patch(before[TARGET])
    assert {p for p in before if before[p] != after[p]} == {TARGET}
    pins = {p:blob(data) for p,data in sorted(after.items())}
    receipt = {
        "feature_id": FEATURE, "parent_castle_blob": prev[TARGET],
        "new_castle_blob": pins[TARGET],
        "source_count":80, "changed_source": [TARGET],
        "other79_byte_identical":True,
        "nonstudio_default":"OFF",
        "private_workspace_attribute":ATTR, "private_attribute_required_before_start":True,
        "nonstudio_max_art_parts":36,"nonstudio_new_lights":0,
        "nonstudio_new_collisions":0,
        "studio_original_appearance":"PRESERVED_SOURCE_ONLY",
        "runtime_live_art":"NOT_TESTED", "android_15min":"NOT_TESTED",
        "art_decision":"ART_NO_GO","live_art_decision":"LIVE_ART_NO_GO",
        "owner_accepted":False,"official_rc_adopted":False,
        "rollback":"omit one extra private overlay; unchanged original castle V3"
    }
    fl["feature_flags"][FEATURE] = True
    fl["source_gitblobs"] = pins
    sl["blobs"] = pins
    fl["live_castle_canary"] = receipt
    sl["live_castle_canary"] = receipt
    tmp = Path(tempfile.mkdtemp(prefix=".p0d_live_castle_",dir=str(out.parent)))
    staged = tmp/"candidate"
    try:
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/TARGET).write_bytes(after[TARGET])
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged) == after and read(base) == before
        os.replace(staged,out)
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
    print("P0D_LIVE_CASTLE_CANARY80_SOURCE_79_PRESERVED_PASS")
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--enabled",choices=("true","false"),required=True)
    args=parser.parse_args()
    apply(args.base,args.out,args.enabled=="true")
