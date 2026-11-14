#!/usr/bin/env python3
"""FB008 cumulative 80/80 source-exact Rojo + authority + rollback receipt."""
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb017_no_guides import read,blob
from apply_fb008_density_rc80 import FEATURE,PATCHED_BLOB,H,BASE_FEATURE

def verify(dist:Path,place:Path,receipt:Path):
    sources=read(dist)
    assert len(sources)==80 and H in sources
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:blob(b) for p,b in sorted(sources.items())}
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert pins[H]==PATCHED_BLOB
    assert fl["feature_flags"][FEATURE] is True
    assert fl["feature_flags"][BASE_FEATURE] is True
    assert fl["fb008_crowd"]["other79_byte_exact"] is True
    expected=collections.Counter(b.decode("utf8") for b in sources.values())
    actual=collections.Counter();names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        prop=item.find("Properties")
        if prop is None:continue
        source=prop.find("string[@name='Source']")
        name=prop.find("string[@name='Name']")
        if source is not None:actual[source.text or ""]+=1
        if name is not None:names[(item.get("class"),name.text)]+=1
    assert expected==actual and sum(actual.values())==80,"ROJO_SOURCE_80_EXACT_REQUIRED"
    assert names[("Script","Game")]==1,"SINGLE_GAME_REQUIRED"
    assert names[("LocalScript","BattleHUDGovernor")]==1
    h=sources[H].decode("utf8")
    assert "local MINIONS = 16" in h and "local MAX_ACTIVE = 17" in h
    assert "minionImpacts<4 and (impactsByPlayer[nearest] or 0)<2" in h
    assert "local separation=Vector3.zero" in h
    report={
       "stage":"SOURCE_CI_VALIDATED_STUDIO_RETEST_REQUIRED",
       "feedback_id":"FB-008",
       "source_scripts":80,"rojo_source_exact":True,"game_singleton":True,
       "other79_unmodified":True,"fb017_guidance_policy_preserved":True,
       "studio_solo_2client_android":"NOT_TESTED","art_acceptance":"NOT_TESTED",
       "place_bytes":place.stat().st_size,
       "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB008_RC80_CROWD_REAL80_ROJO_SOURCE_EXACT_PASS",report["place_bytes"],report["place_sha256"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    x=p.parse_args();verify(x.dist,x.place,x.receipt)
