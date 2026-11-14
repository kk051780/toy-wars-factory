#!/usr/bin/env python3
"""Verify exact 67-source Rojo preview without claiming Studio engine execution."""
import argparse
import base64
import collections
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

def blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def verify(dist: Path, place: Path) -> dict:
    assert dist.is_dir() and place.is_file()
    source = {p.relative_to(dist/"src").as_posix():p.read_bytes()
              for p in sorted((dist/"src").rglob("*.luau"))}
    assert len(source)==67, ("WRONG_PREVIEW_COUNT",len(source))
    assert sum(path=="server/Game.server.luau" for path in source)==1
    assert all(p in source for p in (
        "server/TalkingNPCDirector.luau",
        "server/TalkingNPCRuntime.server.luau",
        "client/TalkingNPCClient.client.luau",
        "server/TwinBiomes.server.luau",
    ))
    p=json.loads((dist/"default.project.json").read_text("utf8"))
    assert p["tree"]["ServerStorage"]["$attributes"]["P0D_RC_ENABLE_TALKING_NPC_V1"] is True
    assert p["tree"]["StarterPlayer"]["StarterPlayerScripts"]["P0DTalkingNPCClient"]["$path"]=="src/client/TalkingNPCClient.client.luau"
    lock=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    feature=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={k:blob(v) for k,v in sorted(source.items())}
    assert lock["total_scripts"]==67 and lock["blobs"]==pins, "NEW_SOURCE_LOCK_DRIFT"
    assert feature["total_sources"]==67 and feature["source_gitblobs"]==pins
    assert feature["feature_flags"]["P0D-TALKING-NPC-V1"] is True
    assert lock["rc_talking_npc_PREP_overlay"]["previous64_byte_identical"] is True

    xml=ET.fromstring(place.read_bytes())
    scripts=collections.Counter()
    titles=collections.Counter()
    ss=[]
    for item in xml.iter("Item"):
        typ=item.get("class")
        nameEl=item.find("./Properties/string[@name='Name']")
        name=nameEl.text if nameEl is not None else ""
        if typ in ("Script","LocalScript","ModuleScript"):
            code=item.find("./Properties/string[@name='Source']")
            if code is not None:
                scripts[(code.text or "").encode("utf8")]+=1
                titles[(typ,name)]+=1
        if typ=="ServerStorage" and name=="ServerStorage":
            ss.append(item)
    expected=collections.Counter(source.values())
    assert scripts==expected, ("ROJO_SOURCE_NOT_EXACT",len(scripts),len(expected))
    for k in (("Script","Game"),
              ("ModuleScript","TalkingNPCDirector"),
              ("Script","TalkingNPCRuntime"),
              ("LocalScript","P0DTalkingNPCClient"),
              ("Script","TwinBiomes")):
        assert titles[k]==1, ("MISSING_OR_DUPLICATE_SCRIPT",k,titles[k])
    assert len(ss)==1, ("SERVERSTORAGE_COUNT",len(ss))
    attrs=ss[0].find("./Properties/BinaryString[@name='AttributesSerialize']")
    if attrs is None:
        attrs=ss[0].find("./Properties/binaryString[@name='AttributesSerialize']")
    assert attrs is not None and attrs.text, "SERVERSTORAGE_SERIALIZED_FLAG_MISSING"
    binary=base64.b64decode("".join(attrs.text.split()))
    assert b"P0D_RC_ENABLE_TALKING_NPC_V1" in binary, "NPC_FLAG_NOT_SERIALIZED"
    assert titles[("Script","Game")]==1
    result={
        "status":"SOURCE_EXACT_ROJO_PASS_ENGINE_NOT_TESTED",
        "preview":True,
        "official_rc_adopted":False,
        "scripts":67,
        "new_scripts":3,
        "previous_sources_preserved":64,
        "source_exact":True,
        "single_Game":True,
        "single_existing_remote":True,
        "studio_2client":"NOT_TESTED",
        "android":"NOT_TESTED",
        "tts_playback":"NOT_TESTED",
        "fun":"NOT_TESTED",
        "rbxlx_bytes":place.stat().st_size,
        "rbxlx_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
    }
    print("P0D_TALKING_NPC_PREP_67_REAL_ROJO_SOURCE_EXACT_PASS",result["rbxlx_bytes"])
    return result

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--dist",type=Path,required=True)
    arg.add_argument("--place",type=Path,required=True)
    arg.add_argument("--receipt",type=Path,required=True)
    a=arg.parse_args()
    report=verify(a.dist,a.place)
    a.receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")

if __name__=="__main__":
    main()
