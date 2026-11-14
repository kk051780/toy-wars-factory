#!/usr/bin/env python3
"""80 exact embedded Rojo source and 7 art scopes: two private opt-in, five NO_GO."""
import argparse,collections,hashlib,json
from pathlib import Path
from defusedxml import ElementTree as ET
from apply_fb015_live_art_client_pilot import read,blob,BEAST,FX,SERVER,CLIENTS,FILES,OLD,NEW,SERVER_OLD,SERVER_NEW,ATTR,OWNER_OPTIN,FLAG,LIVE_CASTLE,CASTLE_BLOB
ART={
 ("Script","CastleDetailArt"):"server/CastleDetailArt.server.luau",
 ("Script","FantasyWorldArt"):"server/FantasyWorldArt.server.luau",
 ("Script","H1CoastalSeascape"):"server/H1CoastalSeascape.server.luau",
 ("Script","H1SeaGroundRepair"):"server/H1SeaGroundRepair.server.luau",
 ("Script","ArtMinionSilhouette"):"server/ArtMinionSilhouette.server.luau",
 ("LocalScript","FB015GoroganVisual"):BEAST,
 ("LocalScript","P0DConfirmedCombatFX"):FX,
}
def verify(base:Path,dist:Path,place:Path,receipt:Path):
    old,new=read(base),read(dist)
    assert len(old)==len(new)==81 and set(old)==set(new)
    changed={p for p in new if old[p]!=new[p]}
    assert changed==set(FILES),("THREE_ONLY",changed)
    assert blob(new[LIVE_CASTLE])==CASTLE_BLOB and old[LIVE_CASTLE]==new[LIVE_CASTLE]
    for p in CLIENTS:
        assert new[p].replace(NEW.encode(),OLD.encode(),1)==old[p]
        assert new[p].count(ATTR.encode())==1
    assert new[SERVER].replace(SERVER_NEW.encode(),SERVER_OLD.encode(),1)==old[SERVER]
    assert new[SERVER].count(OWNER_OPTIN.encode())==1
    assert new[SERVER].count(ATTR.encode())==1
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text())
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text())
    pins={p:blob(v) for p,v in sorted(new.items())}
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert fl["feature_flags"].get(FLAG) is True
    raw=place.read_bytes()
    assert 100000<len(raw)<10000000
    assert b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper()
    names=collections.defaultdict(list);sources=collections.Counter()
    for item in ET.fromstring(raw).iter("Item"):
        typ=item.get("class")
        if typ not in ("Script","LocalScript","ModuleScript"):continue
        ps=item.find("Properties")
        assert ps is not None
        name=ps.find("string[@name='Name']")
        src=ps.find("string[@name='Source']")
        assert name is not None and src is not None
        val=src.text or ""
        names[(typ,name.text or "")].append(val)
        sources[val]+=1
    assert sum(sources.values())==81
    assert sources==collections.Counter(v.decode() for v in new.values())
    assert names[("Script","P0DLiveCastleArt")]==[new[LIVE_CASTLE].decode()]
    assert len(names[("Script","Game")])==1
    assert len(names[("LocalScript","TrapRaidersHUD")])==1
    for key,path in ART.items():
        assert names[key]==[new[path].decode()],("REAL_INSTANCE_DRIFT",key)
        if path in CLIENTS:assert NEW in names[key][0]
        elif path==SERVER:assert SERVER_NEW in names[key][0] and OLD not in names[key][0]
        else:assert OLD in names[key][0],("DANGEROUS_SERVER_ART_ENABLED",path)
    result={
      "schema":"P0D_LIVE_ART_CLIENT_PILOT_RECEIPT_V1",
      "changed_sources":sorted(changed),"other_78_identical":True,
      "exact_studio_place":True,"source_count":81,
      "client_private_optin_sources":2,"server_guarded_art_sources":5,
      "server_private_authorizer":1,
      "studio_visual":"NOT_TESTED","nonstudio_private":"NOT_TESTED",
      "nonstudio_public":"INTENT_OFF_NOT_RUNTIME_TESTED",
      "android15":"NOT_TESTED","kid_fun":"NOT_TESTED",
      "source_gate":"PASS","owner_accepted":False,
      "art_decision":"ART_NO_GO","live_art_decision":"LIVE_ART_NO_GO",
      "mobile_decision":"MOBILE_NO_GO","fun_decision":"FUN_NO_GO",
      "official_rc_adoption":False,"place_bytes":len(raw),
      "place_sha256":hashlib.sha256(raw).hexdigest()
    }
    assert not receipt.exists()
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("P0D_431_RC81_LIVE_CLIENT_SERVER_AUTH_EXACT_PASS__5_STUDIO_ONLY",len(raw),result["place_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for k in ("base","dist","place","receipt"):p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args();verify(a.base,a.dist,a.place,a.receipt)
