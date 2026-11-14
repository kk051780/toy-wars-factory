#!/usr/bin/env python3
"""Source-exact real Rojo RC81 Game/Horde audit for #444 private 9-mob canary."""
from __future__ import annotations
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_live_horde_private import read,blob,GAME,HORDE,FEATURE,PRIVATE_ATTR

def verify(dist:Path,place:Path,receipt:Path):
    src=read(dist);sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert len(src)==sl["total_scripts"]==fl["total_sources"]==81
    pins={p:blob(v) for p,v in sorted(src.items())}
    assert pins==sl["blobs"]==fl["source_gitblobs"],"SOURCE_LOCK_BROKEN"
    assert fl["feature_flags"][FEATURE] is True
    meta=fl["live_horde_private_canary"]
    assert meta["new_game_sha"]==pins[GAME] and meta["other_80_sources_exact"]
    raw=place.read_bytes()
    assert 0<len(raw)<10_000_000 and b"<!DOCTYPE" not in raw.upper()
    assert b"<!ENTITY" not in raw.upper()
    count=collections.Counter()
    named=collections.defaultdict(list)
    for item in ET.fromstring(raw).iter("Item"):
        kind=item.get("class")
        if kind not in {"Script","LocalScript","ModuleScript"}:continue
        props=item.find("Properties")
        if props is None:continue
        name=props.find("string[@name='Name']")
        source=props.find("string[@name='Source']")
        if source is None:continue
        text=source.text or ""
        count[text]+=1
        if name is not None:named[(kind,name.text or "")].append(text)
    assert sum(count.values())==81
    assert count==collections.Counter(v.decode("utf8") for v in src.values())
    for kind,name,path in [
      ("Script","Game",GAME),
      ("ModuleScript","MusouHorde",HORDE),
      ("LocalScript","TrapRaidersHUD","client/HUD.client.luau"),
      ("Script","P0DLiveCastleArt","server/P0DLiveCastleArt.server.luau")
    ]:
        arr=named[(kind,name)]
        assert len(arr)==1 and arr[0]==src[path].decode("utf8"),("AUTHORITY_OR_INSTANCE_DRIFT",name,len(arr))
    game=src[GAME].decode("utf8")
    assert game.count('horde:reset(')==1
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count('workspace:GetAttribute("'+PRIVATE_ATTR+'") == true')==1
    assert game.count('game.PrivateServerId ~= ""')==1
    assert game.count('if RunService:IsStudio() or (')==1
    for banned in ('workspace:SetAttribute("'+PRIVATE_ATTR, 'game.PrivateServerId ='):
        assert banned not in game,("UNSAFE_ENABLER",banned)
    result={
      "schema":"P0D_PRIVATE_LIVE_HORDE_SOURCE_EXACT_81_V1",
      "lua_sources":81,"embedded_sources_exact":81,
      "single_Game":True,"single_MusouHorde":True,"single_HUD":True,
      "one_original_horde_reset_guarded":True,"changed_sources":[GAME],
      "other_80_source_byte_exact":True,
      "server_private_id_and_owner_optin":True,"public_default":"OFF",
      "live_horde_decision":"LIVE_HORDE_NO_GO","owner_accepted":False,
      "real_spawn_9":"NOT_TESTED","real_hits":"NOT_TESTED",
      "art_decision":"ART_NO_GO","mobile_decision":"MOBILE_NO_GO",
      "fun_decision":"FUN_NO_GO","official_rc_adopted":False,
      "place_bytes":len(raw),"place_sha256":hashlib.sha256(raw).hexdigest()
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_PRIVATE_LIVE_HORDE_REAL_ROJO81_EXACT_PASS",result["place_bytes"],result["place_sha256"])
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args();verify(a.dist,a.place,a.receipt)
