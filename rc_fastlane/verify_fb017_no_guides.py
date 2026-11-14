#!/usr/bin/env python3
"""FB017 source-exact Rojo receipt for final RC80 with NO persistent guidance."""
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb017_no_guides import read,blob,TARGET,NEW_SHA,FEATURE
def verify(dist:Path,place:Path,receipt:Path):
    sources=read(dist)
    assert len(sources)==80
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:blob(v) for p,v in sorted(sources.items())}
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["feature_flags"][FEATURE] is True
    assert pins[TARGET]==NEW_SHA
    assert fl["fb017_no_guides"]["79_other_gameplay_sources_byte_exact"] is True
    expected=collections.Counter(data.decode("utf8") for data in sources.values())
    actual=collections.Counter();names=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        p=item.find("Properties")
        if p is None:continue
        x=p.find("string[@name='Source']")
        if x is not None:actual[x.text or ""]+=1
        n=p.find("string[@name='Name']")
        if n is not None:names[(item.get("class"),n.text)]+=1
    assert actual==expected and sum(actual.values())==80,"NOT_ALL_80_EMBEDDED_SOURCES_MATCHED"
    assert names[("Script","Game")]==1
    assert names[("LocalScript","BattleHUDGovernor")]==1
    code=sources[TARGET].decode()
    for s in (
        "noGuidanceActive=true",
        "Score=true", "BattleSelfHPNumerical=true",
        "silenceLabel", "silenceScreen", "silenceWorld",
        'g.Enabled=false',
        "l.Visible=false",
        "restoreLobbyGuideState()",
    ):
        assert s in code,s
    data={
        "source_count":80,
        "all_source_exact":True,
        "single_game":True,
        "owner_feedback":"FB-017",
        "visual_policy":"NO_PERSISTENT_BATTLE_GUIDANCE",
        "other79_unmodified":True,
        "stage":"SOURCE_CI_VALIDATED_STUDIO_RETEST_REQUIRED",
        "studio_ui":"NOT_TESTED",
        "owner_acceptance":"NOT_TESTED",
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB017_RC80_NO_GUIDANCE_ALL80_ROJO_SOURCE_EXACT_PASS",data["place_bytes"],data["place_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
