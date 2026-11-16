#!/usr/bin/env python3
"""Isolated true Rojo 7.7.1 Source/Class proof for the 31 official RC Luau scripts.

Uses byte-exact sources from the original/modified official Place; it does not
replace or author any game logic. No official RC or main branch write.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

def check(ok, why):
    if not ok: raise ValueError("RED_GQ8_ROJO_"+why)

def scripts(place: Path):
    root=ET.fromstring(place.read_bytes())
    result={}
    for item in root.iter("Item"):
        klass=item.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"): continue
        props=item.find("Properties")
        check(props is not None,"MISSING_PROPS")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("string[@name='Source']")
        if source is None:
            source=props.findtext("ProtectedString[@name='Source']")
        check(name and source is not None,"MISSING_NAME_OR_SOURCE")
        check(name not in result,"DUP_NAME")
        result[name]=(klass,source)
    check(len(result)==31,"COUNT_NOT_31")
    return result

def prepare(place: Path, out: Path):
    check(not out.exists(),"OUTPUT_EXISTS")
    out.mkdir(parents=True)
    entries=scripts(place)
    tree={"$className":"DataModel",
          "ServerScriptService":{"$className":"ServerScriptService"},
          "StarterPlayer":{"$className":"StarterPlayer",
            "StarterPlayerScripts":{"$className":"StarterPlayerScripts"}}}
    for name,(klass,source) in sorted(entries.items()):
        if klass=="LocalScript":
            target=tree["StarterPlayer"]["StarterPlayerScripts"]
            ext=".client.luau";where="client"
        else:
            target=tree["ServerScriptService"]
            ext=".server.luau" if klass=="Script" else ".luau"
            where="server"
        check("/" not in name and "\\" not in name and ".." not in name,
              "UNSAFE_NAME")
        path=Path(where)/(name+ext)
        dst=out/"src"/path
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(source,encoding="utf-8")
        target[name]={"$path":str(Path("src")/path).replace("\\","/")}
    project={"name":"GQ8_PRIVATE_RC31_SOURCE_EXACT","tree":tree}
    (out/"default.project.json").write_text(json.dumps(project,indent=2,ensure_ascii=False)+"\n")
    print("GQ8_PRIVATE_ROJO_SOURCE_PROJECT_31_READY")

def verify(expected: Path, actual: Path):
    e=scripts(expected);a=scripts(actual)
    check(e==a,"SOURCE_CLASS_NOT_EXACT")
    print("GQ8_PRIVATE_REAL_ROJO_31_SOURCE_CLASS_EXACT_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="action",required=True)
    b=sub.add_parser("prepare")
    b.add_argument("--place",required=True,type=Path)
    b.add_argument("--out",required=True,type=Path)
    v=sub.add_parser("verify")
    v.add_argument("--expected",required=True,type=Path)
    v.add_argument("--actual",required=True,type=Path)
    a=p.parse_args()
    if a.action=="prepare": prepare(a.place,a.out)
    else: verify(a.expected,a.actual)
