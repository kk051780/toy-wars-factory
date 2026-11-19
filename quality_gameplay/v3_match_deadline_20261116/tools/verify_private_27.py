#!/usr/bin/env python3
"""Independent source-exact Rojo Place verifier for PRIVATE 27-source V3 QA."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

def flatten(manifest, obj, result):
    for name, child in obj.items():
        if name.startswith("$") or not isinstance(child, dict):
            continue
        if "$path" in child:
            assert set(child)=={"$path"}
            assert name not in result, f"duplicate script identity {name}"
            p=(manifest.parent / child["$path"]).resolve(strict=True)
            assert p.is_file() and p.suffix==".luau"
            cls="Script" if p.name.endswith(".server.luau") else (
                "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")
            source=p.read_text(encoding="utf-8").replace("\r\n", "\n")
            result[name]=(cls,source,p)
        else:
            flatten(manifest,child,result)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",type=Path,required=True)
    parser.add_argument("--place",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()
    project=args.project.resolve(strict=True)
    place=args.place.resolve(strict=True)
    receipt=args.receipt.resolve(strict=True)
    tree=json.loads(project.read_text(encoding="utf-8"))["tree"]
    r=json.loads(receipt.read_text(encoding="utf-8"))
    assert r["status"]=="PRIVATE_SOURCE_ONLY_NOT_OFFICIAL_RC"
    assert r["studio"]=="NOT_TESTED" and r["android"]=="NOT_TESTED"
    expected={}
    flatten(project,tree,expected)
    assert len(expected)==r["source_count"]==27
    assert r["server_count"]==24 and r["client_count"]==3
    assert sum(1 for c,_,_ in expected.values() if c=="LocalScript")==3
    assert len(r["source_sha256"])==27
    for name,(_,_,path) in expected.items():
        assert r["source_sha256"][name]==hashlib.sha256(path.read_bytes()).hexdigest(),name

    actual={}
    for node in ET.fromstring(place.read_bytes()).iter("Item"):
        cls=node.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):
            continue
        props=node.find("Properties")
        assert props is not None
        name=props.findtext("string[@name='Name']")
        assert name not in actual,name
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source=props.findtext("string[@name='Source']")
        assert source is not None,("missing Source",name)
        actual[name]=(cls,source.replace("\r\n","\n"))
    ideal={name:(cls,src) for name,(cls,src,_) in expected.items()}
    assert ideal==actual,{
        "missing":sorted(set(ideal)-set(actual)),
        "extra":sorted(set(actual)-set(ideal)),
        "wrong":[n for n in set(ideal)&set(actual) if ideal[n]!=actual[n]]
    }
    host=expected["EGGRUMBLE_LobbyCastleModesPreview"][1]
    assert host.count("DeadlinePolicy.expire(")==1
    assert 'sessions[mode]==session' in host
    assert 'ResultService.showIfFinished(session,queue,mode)' in host
    assert 'RoundReplay.schedule(session,session.closeRound)' in host
    assert 'EGGRUMBLE_NeutralStoneGiant' in host
    score=expected["EGGRUMBLE_MatchResultService"][1]
    assert 'session.rules.winner=="DRAW"' in score
    assert 'ScoreBalance.build(' in score
    assert "EGGRUMBLE_ProceduralSkills" in expected
    assert "EGGRUMBLE_ArtDistanceLOD" in expected
    assert "EGGRUMBLE_FieldItemPickups" in expected
    assert "EGGRUMBLE_BotActors" in expected
    assert "EGGRUMBLE_BossSessionFence" in expected
    digest=hashlib.sha256(place.read_bytes()).hexdigest()
    r["place_sha256"]=digest
    r["place_bytes"]=place.stat().st_size
    receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRIVATE_27_LUAU_ROJO_SOURCE_EXACT_PASS",place.stat().st_size,digest)

if __name__=="__main__":
    main()
