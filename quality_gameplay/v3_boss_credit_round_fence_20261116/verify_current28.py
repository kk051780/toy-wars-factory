#!/usr/bin/env python3
"""Verify Rojo produced 28 original-source-exact Script bodies; issue no Studio claim."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
def walk(project):
    data = json.loads(project.read_text(encoding="utf-8"))["tree"]
    result = {}
    for context, mapped in (
        ("ServerScriptService", data["ServerScriptService"]),
        ("StarterPlayerScripts", data["StarterPlayer"]["StarterPlayerScripts"]),
    ):
        for name, entry in mapped.items():
            if name == "$className":
                continue
            src = (project.parent / entry["$path"]).resolve(strict=True)
            cls = ("Script" if src.name.endswith(".server.luau")
                   else "LocalScript" if src.name.endswith(".client.luau")
                   else "ModuleScript")
            assert name not in result, name
            result[name] = {
                "class": cls, "service": context, "path": str(src),
                "source": src.read_text(encoding="utf-8").replace("\r\n", "\n"),
                "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
            }
    return result

def main():
    parser=argparse.ArgumentParser()
    for key in ("original","project","place","receipt"):
        parser.add_argument("--"+key,required=True,type=Path)
    args=parser.parse_args()
    original=args.original.resolve(strict=True)
    project=args.project.resolve(strict=True)
    place=args.place.resolve(strict=True)
    receipt=args.receipt.resolve()
    authors=walk(original)
    candidate=walk(project)
    assert len(authors)==26 and len(candidate)==28
    assert set(authors).issubset(candidate), "author script missing"
    for name, original_info in authors.items():
        assert candidate[name] == original_info, ("author mapping/content changed",name)
    extra=set(candidate)-set(authors)
    assert extra=={"EGGRUMBLE_BossCreditPolicy","EGGRUMBLE_BossCreditRoundFence"},extra
    observed={}
    for item in ET.parse(place).iter("Item"):
        cls=item.attrib.get("class")
        if cls not in {"Script","ModuleScript","LocalScript"}:continue
        props=item.find("Properties")
        if props is None:continue
        name=props.find("string[@name='Name']")
        if name is None or not name.text:continue
        source=props.find("ProtectedString[@name='Source']")
        if source is None:source=props.find("string[@name='Source']")
        assert name.text not in observed, "duplicate script in Place"
        observed[name.text]={"class":cls,"source":(source.text or "").replace("\r\n","\n") if source is not None else None}
    assert set(observed)==set(candidate),(set(candidate)-set(observed),set(observed)-set(candidate))
    for name, expected in candidate.items():
        assert observed[name]["class"]==expected["class"],("class mismatch",name)
        assert observed[name]["source"]==expected["source"],("source mismatch",name)
    result={
        "status":"NON_PUBLIC_GQ_SOURCE_EXACT_28_ONLY",
        "original_composer_source_count":26,
        "added_optional_server_sources":2,
        "actual_place_source_count":28,
        "original26_unchanged":True,
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
        "sources":{n:{"sha256":z["sha256"],"class":z["class"],"service":z["service"]} for n,z in sorted(candidate.items())},
        "official_rc_integration":False,
        "real_studio":"NOT_TESTED","android":"NOT_TESTED","owner":"NO_GO",
    }
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("CURRENT28_GQ_SOURCE_EXACT_28_OF_28_PASS",result["place_bytes"],result["place_sha256"])
if __name__=="__main__":
    main()
