#!/usr/bin/env python3
"""Reuse #484's exact original GAME+ART+SCORE private26 composer, overlay ONLY GQ520 ridge.

No new Game, bot, ART, SCORE, ITEM or Rojo composer. Never update original author sources.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from patch_ridge import OLD, NEW, ORIGINAL_GIT_BLOB, git_blob, patch_author_host

HOST = "EGGRUMBLE_LobbyCastleModesPreview"
EXPECTED = 26

def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def scripts(project: Path, expected_count=EXPECTED):
    project=project.resolve(strict=True)
    obj=json.loads(project.read_text(encoding="utf-8"))
    if obj.get("tree",{}).get("$className")!="DataModel":
        raise ValueError("RED: unexpected Rojo project")
    result={}
    def descend(node,chain=()):
        if not isinstance(node,dict):
            return
        if "$path" in node:
            if set(node)!={"$path"}:
                raise ValueError("RED: duplicate mixed script authority")
            name=chain[-1]
            if name in result:
                raise ValueError("RED: repeated script name "+name)
            f=(project.parent/node["$path"]).resolve(strict=True)
            cls="Script" if f.name.endswith(".server.luau") else (
                "LocalScript" if f.name.endswith(".client.luau") else "ModuleScript"
            )
            result[name]=(chain,f,cls,node)
        else:
            for name,child in node.items():
                if not name.startswith("$"):
                    descend(child,chain+(name,))
    descend(obj["tree"])
    if len(result)!=expected_count or HOST not in result or result[HOST][2]!="Script":
        raise ValueError("RED: base source/host contract drift")
    return obj,result

def original_composed_host(author: str, quality: str, composer: Path) -> str:
    modspec=importlib.util.spec_from_file_location("gq520_original_484_composer",composer)
    if modspec is None or modspec.loader is None:
        raise ValueError("RED: cannot load original #484 composer")
    mod=importlib.util.module_from_spec(modspec)
    modspec.loader.exec_module(mod)
    return mod.apply_ramp(author,quality)

def patch_composed_host(existing: str, author: str, quality: str,
                        item: str, expected_compose) -> str:
    """Exact compare keeps #484 castle ramp; only existing TEAM terrain is rewritten."""
    base_patch=patch_author_host(author,item)
    expected=expected_compose(author,quality)
    if existing!=expected:
        raise ValueError("RED: #484 author-composed host drift, must reconcile")
    if existing.count(OLD)!=1 or base_patch.count(NEW)!=1:
        raise ValueError("RED: terrain anchor drift")
    result=existing.replace(OLD,NEW)
    if result.replace(NEW,OLD)!=existing:
        raise ValueError("RED: patch not one-block-reversible")
    if result.count("CastleAccessRamp")!=existing.count("CastleAccessRamp"):
        raise ValueError("RED: preexisting #484 castle access ramp lost")
    return result

def prepare(base:Path, base_receipt:Path, author_host:Path, quality_host:Path,
            item:Path, quality_composer:Path, outdir:Path)->Path:
    if not base.exists() or not base_receipt.exists():
        raise ValueError("RED: source-exact #484 base project/receipt missing")
    base=base.resolve(strict=True)
    author_host=author_host.resolve(strict=True)
    quality_host=quality_host.resolve(strict=True)
    item=item.resolve(strict=True)
    quality_composer=quality_composer.resolve(strict=True)
    outdir=outdir.resolve()
    for source in (base,author_host,quality_host,item,quality_composer):
        if outdir == source or source.is_relative_to(outdir):
            raise ValueError("RED: output directory collides with original author")
    if outdir==base.parent:
        raise ValueError("RED: private overlay must use distinct directory")
    obj, original=scripts(base)
    receipt=json.loads(base_receipt.read_text(encoding="utf-8"))
    old_hashes=receipt.get("source_sha256",{})
    if set(old_hashes)!=set(original):
        raise ValueError("RED: #484 source receipt incomplete/mismatch")
    for name,(_,f,_,_) in original.items():
        if sha_file(f)!=old_hashes[name]:
            raise ValueError("RED: #484 source receipt hash mismatch "+name)
    author=author_host.read_text(encoding="utf-8")
    if git_blob(author)!=ORIGINAL_GIT_BLOB:
        raise ValueError("RED: author original host lock mismatch")
    existing=original[HOST][1].read_text(encoding="utf-8")
    patched=patch_composed_host(existing,author,quality_host.read_text(encoding="utf-8"),
        item.read_text(encoding="utf-8"),
        lambda a,q:original_composed_host(a,q,quality_composer))
    outdir.mkdir(parents=True,exist_ok=True)
    generated=outdir/"EGGRUMBLE_LobbyCastleModesPreview.private.server.luau"
    generated.write_text(patched,encoding="utf-8")
    current=copy.deepcopy(obj)
    # The original #484 project lives one directory ABOVE this isolated output.
    # Rebase every path (not its file contents) so Rojo resolves the same 25 owners.
    for name,(chain,source_path,_,_) in original.items():
        node=current["tree"]
        for key in chain:
            node=node[key]
        chosen=generated if name==HOST else source_path
        node["$path"]=Path(os.path.relpath(chosen,outdir)).as_posix()
    current["name"]="GQ520_AUTHOR26_RIDGE_ONLY_UNPUBLISHED_NOT_OFFICIAL_RC"
    project=outdir/"GQ520_RIDGE_AUTHOR26.project.json"
    project.write_text(json.dumps(current,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _, mapped=scripts(project)
    if original.keys()!=mapped.keys():
        raise ValueError("RED: 26 script set changed")
    for name,(_,f,cls,_) in original.items():
        if mapped[name][2]!=cls:
            raise ValueError("RED: script class changed "+name)
        if name!=HOST and (mapped[name][1]!=f or sha_file(mapped[name][1])!=old_hashes[name]):
            raise ValueError("RED: non-host original author script changed "+name)
    detail={
      "status":"PRIVATE26_SOURCE_ONLY_NO_OFFICIAL_RC_WRITE",
      "source_count":EXPECTED,"unchanged_source_count":25,
      "one_overlay":"EGGRUMBLE_LobbyCastleModesPreview.CentralRidge_COLLISION_ONLY",
      "original_author_host_git_blob":ORIGINAL_GIT_BLOB,
      "original_author_21_head":"fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
      "quality_484_head":"6b52eaf1f2725496277998fe0c5532b7a8fcaab5",
      "art_485_head":"e86702c906bdf9c71adcdf769ae48a206b26607b",
      "score_487_head":"438a406ccfda5563053d783d7561797ccd364361",
      "source_sha256":{name:sha_file(path) for name,(_,path,_,_) in sorted(mapped.items())},
      "official_rc_adopted":0, "studio":"NOT_TESTED","android":"NOT_TESTED","owner":"NO_GO",
    }
    (outdir/"GQ520_PRIVATE26_RECEIPT.json").write_text(
        json.dumps(detail,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ520_ORIGINAL_484_26SOURCE_REUSE_ONE_RIDGE_OVERLAY_PASS",len(mapped))
    return project

def verify(project:Path,place:Path):
    _,mapped=scripts(project)
    actual={}
    for x in ET.parse(place).getroot().iter("Item"):
        klass=x.get("class")
        if klass not in {"Script","LocalScript","ModuleScript"}:
            continue
        props=x.find("Properties")
        if props is None:
            continue
        name=props.findtext("string[@name='Name']")
        body=props.findtext("ProtectedString[@name='Source']")
        if body is None:
            body=props.findtext("string[@name='Source']")
        if not name or body is None or name in actual:
            raise ValueError("RED: missing/duplicate Rojo script "+str(name))
        actual[name]=(klass,body.replace("\r\n","\n"))
    if set(actual)!=set(mapped) or len(actual)!=EXPECTED:
        raise ValueError("RED: Rojo script count/names mismatch")
    receipt_file=project.parent/"GQ520_PRIVATE26_RECEIPT.json"
    receipt=json.loads(receipt_file.read_text(encoding="utf-8"))
    for name,(_,source,klass,_) in mapped.items():
        data=source.read_text(encoding="utf-8").replace("\r\n","\n")
        if actual[name]!=(klass,data) or sha_file(source)!=receipt["source_sha256"][name]:
            raise ValueError("RED: Rojo native source/class/hash drift "+name)
    receipt["place_bytes"]=place.stat().st_size
    receipt["place_sha256"]=sha_file(place)
    receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ520_26_26_REAL_ROJO_SOURCE_CLASS_EXACT_PASS",
          receipt["place_bytes"],receipt["place_sha256"])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    subs=parser.add_subparsers(dest="action",required=True)
    c=subs.add_parser("prepare")
    for name in ("base","base_receipt","author_host","quality_host","item",
                 "quality_composer","outdir"):
        c.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    v=subs.add_parser("verify")
    for name in ("project","place"):
        v.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    if args.action=="prepare":
        prepare(args.base,args.base_receipt,args.author_host,args.quality_host,
                args.item,args.quality_composer,args.outdir)
    else:verify(args.project,args.place)
if __name__=="__main__":main()
