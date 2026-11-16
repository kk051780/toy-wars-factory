#!/usr/bin/env python3
"""Rebuild a read-only 31-script source project from the *verified official RC*
Studio Place + exact original-author manifest in one pinned Actions artifact.

No gameplay reimplementation: every original Script Source is extracted
unchanged and checked against its native author SHA256 before any overlay.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--place",type=Path,required=True)
    ap.add_argument("--project",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    manifest=json.loads(a.receipt.read_text(encoding="utf-8"))
    if manifest.get("source_count")!=31 or manifest.get("real_rojo_source_class_exact_31") is not True:
        raise ValueError("RED_OFFICIAL_RC31_ARTIFACT_RECEIPT_INCONSISTENT")
    if not a.place.is_file() or a.place.stat().st_size!=240416:
        raise ValueError("RED_PINNED_RC31_PLACE_BYTE_SIZE_CHANGED")
    raw=ET.fromstring(a.place.read_bytes())
    embedded={}
    for item in raw.iter("Item"):
        cls=item.attrib.get("class")
        if cls not in {"Script","ModuleScript","LocalScript"}: continue
        props=item.find("Properties")
        if props is None: raise ValueError("RED_MISSING_SCRIPT_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None: source=props.findtext("string[@name='Source']")
        if not name or source is None or name in embedded:
            raise ValueError("RED_MISSING_OR_DUPLICATE_SCRIPT_NAME")
        embedded[name]=(cls,source.replace("\r\n","\n"))
    if len(embedded)!=31:
        raise ValueError("RED_NOT_EXACTLY_31_ORIGINAL_SCRIPT_SOURCES")
    document=json.loads(a.project.read_text(encoding="utf-8"))
    scripts=[]
    def visit(node,prefix=()):
        for name,attr in node.items():
            if name.startswith("$"): continue
            if not isinstance(attr,dict):raise ValueError("RED_BAD_ROJO_NODE")
            key=prefix+(name,)
            if "$path" in attr:
                if set(attr)!={"$path"}:
                    raise ValueError("RED_UNSAFE_ROJO_PATH_PROPERTIES")
                scripts.append((key,attr))
            else:
                visit(attr,key)
    visit(document["tree"])
    if len(scripts)!=31 or {x[0][-1] for x in scripts}!=set(embedded):
        raise ValueError("RED_PROJECT_AND_RC_PLACE_SCRIPT_NAMES_DIFFER")
    a.out.mkdir(parents=True,exist_ok=True)
    for key,node in scripts:
        n=key[-1]
        clazz,src=embedded[n]
        old=Path(node["$path"]).name
        expected=("Script" if old.endswith(".server.luau") else
                  "LocalScript" if old.endswith(".client.luau") else "ModuleScript")
        if clazz!=expected:
            raise ValueError("RED_AUTHOR_SCRIPT_CLASS_CHANGED "+n)
        if sha(src.encode("utf-8"))!=manifest["source_sha256"].get("/".join(key)):
            raise ValueError("RED_EMBEDDED_AUTHOR_SHA_MISMATCH "+n)
        filename=n+(".server.luau" if clazz=="Script" else
                    ".client.luau" if clazz=="LocalScript" else ".luau")
        (a.out/filename).write_bytes(src.encode("utf-8"))
        node["$path"]=filename
    output=a.out/"BASE31_FROM_OFFICIAL_RC.project.json"
    output.write_text(json.dumps(document,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={
      "original_rc_build_head":"935e50f6e590c3bd783e2dc8aac947627f57fd5f",
      "original_rc_build_run":43852865328,
      "original_place_bytes":a.place.stat().st_size,
      "original_place_sha256":sha(a.place.read_bytes()),
      "original_31_sources_exact":True,
      "original_author_receipt_sha256":sha(a.receipt.read_bytes()),
      "source_only_rebuild":True,
      "official_rc_modified":False
    }
    (a.out/"SOURCE_ORIGIN.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print("GQ540_OFFICIAL_RC31_ORIGINAL_AUTHOR_SOURCE_EXACT_EXTRACTION_PASS",len(scripts))

if __name__=="__main__":main()
