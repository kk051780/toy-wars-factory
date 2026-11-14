#!/usr/bin/env python3
"""P0 #431: independent full Rojo 80-source, object identity, mobile-safe receipt."""
from __future__ import annotations
import argparse,collections,hashlib,json
from pathlib import Path
from defusedxml import ElementTree as DET
from apply_fb015_live_combat_fx import TARGET,BASE_BLOB,FEATURE,read,blob

CRITICAL=(
 ("Script","Game","server/Game.server.luau"),
 ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
 ("LocalScript","P0DConfirmedCombatFX",TARGET),
 ("LocalScript","BattleHUDGovernor","client/BattleHUDGovernor.client.luau"),
 ("Script","FantasyWorldArt","server/FantasyWorldArt.server.luau"),
 ("Script","CastleDetailArt","server/CastleDetailArt.server.luau"),
)

def verify(dist:Path,place:Path,receipt:Path)->dict:
    src=read(dist)
    assert len(src)==80 and TARGET in src, "FULL_REAL80_REQUIRED"
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:blob(v) for p,v in sorted(src.items())}
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"].get(FEATURE) is True
    meta=fl["live_combat_fx"]
    assert meta["original_blob"]==BASE_BLOB
    assert meta["new_blob"]==pins[TARGET]
    assert meta["other79_byte_exact"] is True
    assert meta["source_count"]==80
    raw=place.read_bytes()
    assert len(raw)<12_000_000 and b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper()
    expected=collections.Counter(z.decode("utf8") for z in src.values())
    actual=collections.Counter()
    named=collections.defaultdict(list)
    count=0
    for item in DET.fromstring(raw).iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):
            continue
        count+=1
        props=item.find("Properties")
        assert props is not None,"SOURCELESS_SCRIPT"
        name=props.find("string[@name='Name']")
        body=props.find("string[@name='Source']")
        assert name is not None and body is not None and name.text,"NAME_OR_SOURCE_MISSING"
        code=body.text or ""
        actual[code]+=1
        named[(kind,name.text)].append(code)
    assert count==80 and actual==expected,"ROJO_80_EMBEDDED_SOURCE_MISMATCH"
    for kind,name,path in CRITICAL:
        values=named[(kind,name)]
        assert len(values)==1 and values[0]==src[path].decode("utf8"),("SOURCE_OR_INSTANCE_SWAPPED",name)
    fx=src[TARGET].decode("utf8")
    assert 'if not RunService:IsStudio() then return end' not in fx
    assert 'local MAX_ACTIVE_PARTS = if touchDevice then 16 else 32' in fx
    assert 'local VIEW_DISTANCE = if touchDevice then 70 else 110' in fx
    assert 'popup:GetPropertyChangedSignal("Enabled"):Connect(' in fx
    assert 'FB008_CONFIRMED_HIT_SLASH_VFX_ATTACHED_LIVE_PARITY_ART_NO_GO' in fx
    for banned in ("FireServer(", "TakeDamage(", "CanCollide = true","CanQuery = true",
                   'Instance.new("ScreenGui")'):
        assert banned not in fx,("UNSAFE_CLIENT_FX",banned)
    result={
        "schema":"P0D_LIVE_ART_COMBAT_FX_SOURCE_PARITY_V1",
        "original_studio_only_layers":7,
        "live_enabled_candidate_layers":1,
        "other_six_studio_only_layers":"UNMODIFIED",
        "source_count":80,"source_exact":True,
        "critical_instance_source_exact":True,
        "other79_byte_exact":True,
        "original_game_remote_horde_unchanged":True,
        "mobile_max_effect_parts":16,
        "mobile_max_effect_distance_studs":70,
        "preview_only_candidate":True,"official_rc_adopted":False,
        "studio_pc":"NOT_TESTED","private_live_test":"NOT_TESTED",
        "android_real_15min":"NOT_TESTED","kid_fun":"FUN_NO_GO",
        "art":"ART_NO_GO","live_art":"LIVE_ART_NO_GO",
        "owner_accepted":False,
        "place_bytes":len(raw),
        "place_sha256":hashlib.sha256(raw).hexdigest(),
        "rollback":"omit source overlay, restore original fixed 80"
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_P431_LIVE_COMBAT_FX_REAL80_SOURCE_EXACT_PASS",result["place_bytes"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
