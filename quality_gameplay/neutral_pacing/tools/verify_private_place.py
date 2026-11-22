#!/usr/bin/env python3
"""Independent source-exact validation of the actual Rojo-built private .rbxlx."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

def verify(stage: Path, place: Path) -> dict:
    stage=stage.resolve(strict=True)
    place=place.resolve(strict=True)
    from sys import path
    path.insert(0, str(Path(__file__).resolve().parent))
    from compose_private_v3 import entries
    project=json.loads((stage/"EGGRUMBLE_V3_NEUTRAL_PACING.project.json").read_text(encoding="utf-8"))
    manifest=json.loads((stage/"SOURCE_LOCK_RECEIPT.json").read_text(encoding="utf-8"))
    expected=entries(project)
    assert len(expected)==22
    assert manifest["original_sources_byte_exact"]==20
    assert manifest["original_sources_surgical_change"]==1
    assert manifest["author_head"]=="fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
    source = {}
    for key, relative in expected.items():
        f=(stage/relative).resolve(strict=True)
        assert f.is_relative_to(stage)
        cls="Script" if f.name.endswith(".server.luau") else ("LocalScript" if f.name.endswith(".client.luau") else "ModuleScript")
        assert key[-1] not in source, "duplicate code name"
        source[key[-1]]=(cls,f.read_text(encoding="utf-8").replace("\r\n","\n"))
    assert len(source)==22

    xml=ET.parse(place).getroot()
    actual={}
    for elem in xml.iter("Item"):
        cls=elem.attrib.get("class")
        if cls not in {"Script","LocalScript","ModuleScript"}:
            continue
        p=elem.find("Properties")
        assert p is not None
        name=p.findtext("string[@name='Name']")
        code=p.findtext("ProtectedString[@name='Source']")
        if code is None:
            code=p.findtext("string[@name='Source']")
        assert name and code is not None, "missing code node"
        assert name not in actual, ("shadow script", name)
        actual[name]=(cls,code.replace("\r\n","\n"))
    assert actual==source, "actual Place code or Class differs from authored Rojo sources"
    assert len(actual)==22
    assert sum(cls=="Script" for cls,_ in actual.values())==1
    assert sum(cls=="LocalScript" for cls,_ in actual.values())==2
    assert sum(cls=="ModuleScript" for cls,_ in actual.values())==19
    horde=source["EGGRUMBLE_SwarmCombat"][1]
    assert horde.count('SpawnPacing.step(')==1 and horde.count('h.Died:Connect(')==1
    assert 'SPAWN_BATCH=5' not in horde
    assert "NEUTRAL_PACING_NATIVE_PASS" not in horde
    details={
        "schema":"P0D_NEUTRAL_PRIVATE_SOURCE_EXACT_V1",
        "candidate_source_exact":22,
        "author_base_sources_unchanged":20,
        "author_swarm_splices":1,
        "new_pacing_module":1,
        "classes":{"Script":1,"ModuleScript":19,"LocalScript":2},
        "place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
        "author_head":manifest["author_head"],
        "official_rc_integrated":False,
        "studio_tested":False,
        "android_tested":False,
        "owner_accepted":False,
    }
    (stage/"PRIVATE_PLACE_RECEIPT.json").write_text(json.dumps(details,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("EGGRUMBLE_NEUTRAL_PACING_PRIVATE_ROJO_SOURCE_EXACT_PASS 22/22")
    print("PRIVATE_PLACE_BYTES",details["place_bytes"],"SHA256",details["place_sha256"])
    return details

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--stage",required=True,type=Path)
    ap.add_argument("--place",required=True,type=Path)
    args=ap.parse_args()
    verify(args.stage,args.place)
