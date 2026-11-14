#!/usr/bin/env python3
"""Real 78/78 Rojo XML source exact + singleton original Game for robust lobby."""
from __future__ import annotations
import argparse,collections,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from apply_p0_motion78 import read,gitblob
from apply_p0_recovery_v2_78 import GAME,ID
def verify(dist:Path,place:Path,receipt:Path):
    source=read(dist)
    assert len(source)==78
    sl=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={k:gitblob(v) for k,v in sorted(source.items())}
    assert sl["total_scripts"]==fl["total_sources"]==78
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["p0_recovery_v2_78"]["id"]==ID
    assert fl["p0_recovery_v2_78"]["other77_scripts_byte_exact"]
    assert fl["p0_spectator_h2_78"]["other76_byte_exact"]
    script=source[GAME].decode("utf8")
    assert script.count('local function scheduleLobbyRecovery(')==1
    assert script.count('scheduleLobbyRecovery(p)')==1
    assert script.count('scheduleLobbyRecovery(entrant)')==1
    expected=collections.Counter(v.decode("utf8") for v in source.values())
    actual=collections.Counter()
    classes=collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script","ModuleScript","LocalScript"):continue
        code=item.find("./Properties/string[@name='Source']")
        if code is not None: actual[code.text or ""]+=1
        name=item.find("./Properties/string[@name='Name']")
        if name is not None: classes[(item.get("class"),name.text)]+=1
    assert actual==expected and sum(actual.values())==78
    assert classes[("Script","Game")]==1
    assert classes[("ModuleScript","SoloTeamBots")]==1
    assert classes[("LocalScript","P0DNeutralMotion")]==1
    report={
        "candidate":"P0D_PRIVATE78_ALL_GAME_ART_RECOVERY_V2",
        "scripts":78,"unique_game":True,"all_source_exact":True,
        "pr393_safe_respawn":"AUTHORED_EXACT_HELPER+SOURCE_NATIVE_QA",
        "parent_78_byte_unchanged":True,
        "official_adoption":0,"owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
        "studio_engine":"NOT_TESTED","android_fps":"NOT_TESTED",
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest()}
    receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0_PRIVATE78_RECOVERY_V2_ROJO_78_78_SOURCE_EXACT_PASS",
          report["place_bytes"],report["place_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
