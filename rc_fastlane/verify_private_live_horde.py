#!/usr/bin/env python3
"""P0 #444 verify 81 compiled real Rojo sources; never infer live approval."""
from __future__ import annotations
import argparse,collections,hashlib,json
from pathlib import Path
from defusedxml import ElementTree as ET
from apply_private_live_horde import GAME,HORDE,OPT_IN,FEATURE,read,blob,OLD,NEW

def verify(dist:Path,place:Path,receipt:Path):
    sources=read(dist)
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text())
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text())
    pins={k:blob(v) for k,v in sorted(sources.items())}
    assert len(sources)==sl["total_scripts"]==fl["total_sources"]==81
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    assert fl["private_live_horde"]["new_authority_git_blob"]==pins[GAME]
    assert fl["private_live_horde"]["other80_sources_byte_exact"] is True
    raw=place.read_bytes()
    assert 0<len(raw)<10_000_000 and b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper()
    actual=collections.Counter()
    by_name=collections.defaultdict(list)
    for item in ET.fromstring(raw).iter("Item"):
        k=item.get("class")
        if k not in ("Script","LocalScript","ModuleScript"):continue
        ps=item.find("Properties")
        if ps is None:continue
        code=ps.find("string[@name='Source']")
        nm=ps.find("string[@name='Name']")
        if code is None or nm is None:continue
        v=code.text or ""
        actual[v]+=1
        by_name[(k,nm.text)].append(v)
    assert actual==collections.Counter(v.decode() for v in sources.values())
    assert sum(actual.values())==81,"NOT_81_EXACT_EMBEDDED_LUAU"
    expected=(
        ("Script","Game",GAME),
        ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
        ("LocalScript","BattleHUDGovernor","client/BattleHUDGovernor.client.luau"),
        ("Script","P0DLiveCastleArt","server/P0DLiveCastleArt.server.luau")
    )
    for k,nm,p in expected:
        assert by_name[(k,nm)]==[sources[p].decode()],("SINGLE_AUTHOR_RUNTIME_SOURCE_MISMATCH",nm)
    game=sources[GAME].decode()
    assert OLD not in game and game.count(NEW)==1
    assert game.count('remote.OnServerEvent:Connect(')==1
    report={
      "schema":"P0D_PRIVATE_LIVE_HORDE81_PLACE_EXACT_V1",
      "source_count":81,"embedded_exact":81,
      "source_changed":[GAME],"other80_byte_exact":True,
      "MusouHorde_original":True,
      "private_optin":"SOURCE_ONLY_NOT_ENGINE_TESTED",
      "public_nonstudio":"UNCHANGED_OFF",
      "actual_nine_neutral_mobs":"NOT_TESTED",
      "confirmed_damage_popup":"NOT_TESTED",
      "android15min":"NOT_TESTED","kid_fun":"NOT_TESTED",
      "art_decision":"ART_NO_GO","live_art_decision":"LIVE_ART_NO_GO",
      "mobile_decision":"MOBILE_NO_GO","fun_decision":"FUN_NO_GO",
      "owner_accepted":False,"publish_approved":False,
      "place_bytes":len(raw),"place_sha256":hashlib.sha256(raw).hexdigest()
    }
    receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_PRIVATE_HORDE_81_EXACT_SOURCE_PASS",len(raw))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
