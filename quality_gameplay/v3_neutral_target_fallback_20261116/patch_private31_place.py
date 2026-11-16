#!/usr/bin/env python3
"""Apply #542 ONE original Swarm correction to #530's already source-verified
unpublished 31-source Rojo Place. Does not contact/modify the official RC.
This is an XML-derived PRIVATE Playtest candidate, not a fresh Rojo build.
"""
from __future__ import annotations
import argparse, hashlib, json, xml.etree.ElementTree as ET
from pathlib import Path
from compose_fallback import apply, sha256

PARENT_RUN=43847278518
PARENT_ARTIFACT=14216012082
TARGET="EGGRUMBLE_SwarmCombat"
KINDS={"Script","ModuleScript","LocalScript"}

def scripts(root):
    found={}
    for item in root.iter("Item"):
        kind=item.attrib.get("class")
        if kind not in KINDS:continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_MISSING_PROPERTIES")
        values={child.get("name"):child for child in props}
        name=values.get("Name")
        source=values.get("Source")
        if name is None or source is None or not name.text or name.text in found:
            raise ValueError("RED_DUPLICATE_OR_MISSING_NAME_SOURCE")
        found[name.text]=(kind,source)
    return found

def compose(parent:Path,manifest:Path,out:Path,source_out:Path)->dict:
    if out.exists() or source_out.exists(): raise ValueError("RED_NO_OVERWRITE")
    raw=parent.read_bytes()
    rec=json.loads(manifest.read_text(encoding="utf-8"))
    if rec.get("official_rc_adopted") is not False or rec.get("source_count")!=31:
        raise ValueError("RED_UNTRUSTED_PARENT_RECEIPT")
    if not rec.get("real_rojo_source_class_exact_31"):
        raise ValueError("RED_PARENT_ROJO_NOT_VERIFIED")
    if rec.get("private_place_sha256")!=sha256(raw) or rec.get("private_place_bytes")!=len(raw):
        raise ValueError("RED_PARENT_PLACE_HASH_OR_LENGTH")
    try:root=ET.fromstring(raw)
    except ET.ParseError as exc:raise ValueError("RED_NOT_XML_PLACE") from exc
    original=scripts(root)
    if len(original)!=31 or TARGET not in original:
        raise ValueError("RED_NOT_ORIGINAL_31")
    old=original[TARGET][1].text or ""
    fresh=apply(old)
    original[TARGET][1].text=fresh
    after=scripts(root)
    if set(after)!=set(original):raise ValueError("RED_SCRIPT_MAPPING_CHANGED")
    changed=[]
    for name,(kind,content) in after.items():
        expected_kind,original_content=original[name]
        if kind!=expected_kind:raise ValueError("RED_CLASS_CHANGED")
        if (content.text or "")!=(old if name==TARGET else (original_content.text or "")):
            changed.append(name)
    if changed!=[TARGET]:raise ValueError("RED_OTHER_AUTHORITY_CHANGED "+repr(changed))
    if (after[TARGET][1].text or "")!=fresh:raise ValueError("RED_SWARM_NOT_APPLIED")
    out.parent.mkdir(parents=True,exist_ok=True)
    source_out.parent.mkdir(parents=True,exist_ok=True)
    bytes_out=ET.tostring(root,encoding="utf-8",xml_declaration=True)
    out.write_bytes(bytes_out)
    source_out.write_text(fresh,encoding="utf-8")
    decoded=scripts(ET.fromstring(out.read_bytes()))
    if set(decoded)!=set(original) or len(decoded)!=31:
        raise ValueError("RED_REPARSE_LOST_SCRIPTS")
    for name,(kind,content) in decoded.items():
        if kind!=original[name][0] or (content.text or "") != (fresh if name==TARGET else (original[name][1].text or "")):
            raise ValueError("RED_XML_SOURCE_DRIFT "+name)
    return {
        "parent_run":PARENT_RUN,"parent_artifact":PARENT_ARTIFACT,
        "verified_parent_place_sha256":sha256(raw),
        "new_private_place_sha256":sha256(bytes_out),
        "new_private_place_bytes":len(bytes_out),
        "source_count":31,
        "unchanged_other_sources":30,
        "one_existing_swarm_modified":True,
        "original_author_solutions_reused":True,
        "fresh_rojo_build":False,
        "fresh_native_compile":False,
        "studio_android_tested":False,
        "official_rc_integrated":False
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--swarm-out",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(compose(a.parent,a.receipt,a.out,a.swarm_out),indent=2))
