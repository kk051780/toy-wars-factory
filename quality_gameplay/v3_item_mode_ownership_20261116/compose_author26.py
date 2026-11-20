#!/usr/bin/env python3
"""Overlay source-selected #489+#517+#525 changes into existing #484 original26.

The #484 composer remains the one and only 26-script author. This file
changes exactly two SCRIPT SOURCES in a scratch Rojo project; no new Game,
Remote, item service, rules authority or official RC branch writes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patch_sources as own

GAME = "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
HOST = "EGGRUMBLE_LobbyCastleModesPreview"
ITEM = "EGGRUMBLE_FieldItemPickups"
EXPECTED = 26
AUTHOR_482 = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
AUTHOR_484 = "6b52eaf1f2725496277998fe0c5532b7a8fcaab5"
AUTHOR_485 = "e86702c906bdf9c71adcdf769ae48a206b26607b"
AUTHOR_487 = "438a406ccfda5563053d783d7561797ccd364361"
AUTHOR_489 = "03c51bf5c8d12484bd8dc4667b0d3d3841cb4ddd"
AUTHOR_517 = "c8a324ad7bb40648d82a5828cbf54e217585fefd"

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def scripts(project: Path) -> dict:
    tree = json.loads(project.read_text(encoding="utf-8"))["tree"]
    found: dict = {}
    def walk(node, chain):
        if not isinstance(node,dict):
            return
        if "$path" in node:
            name = chain[-1]
            if name in found:
                raise ValueError(f"duplicated script name: {name}")
            found[name] = (chain, (project.parent/node["$path"]).resolve(strict=True))
        else:
            for k,v in node.items():
                if not k.startswith("$"):
                    walk(v,chain+(k,))
    walk(tree,())
    if len(found)!=EXPECTED:
        raise ValueError(f"expected 26 scripts, got {len(found)}")
    if found[HOST][0] != ("ServerScriptService",HOST):
        raise ValueError("host Script location changed")
    if found[ITEM][0] != ("ServerScriptService",ITEM):
        raise ValueError("item ModuleScript location changed")
    return found

def load_heal(path: Path):
    spec=importlib.util.spec_from_file_location("author517_heal",path)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.ORIGINAL_ITEM_GIT_BLOB != own.ORIGINAL_ITEM_BLOB:
        raise ValueError("HEAL original ITEM owner mismatch")
    return module

def compose(base_project: Path, base_receipt: Path, item_author: Path,
            heal_patch: Path, output_project: Path, output_receipt: Path) -> None:
    base=scripts(base_project)
    original_item=item_author.read_bytes()
    if own.git_blob_sha(original_item)!=own.ORIGINAL_ITEM_BLOB:
        raise ValueError("original #489 ITEM blob mismatch")
    receipt=json.loads(base_receipt.read_text(encoding="utf-8"))
    if receipt.get("script_count")!=EXPECTED:
        raise ValueError("original #484 compositor receipt mismatch")
    if set(receipt["source_sha256"])!=set(base):
        raise ValueError("original #484 compositor source names mismatch")
    for name,(_,path) in base.items():
        if receipt["source_sha256"][name]!=sha(path.read_bytes()):
            raise ValueError(f"original #484 receipt drift at {name}")
    host_original=base[HOST][1].read_text(encoding="utf-8")
    if "CastleAccessRamp" not in host_original:
        raise ValueError("original #484 castle access ramp missing")
    heal=load_heal(heal_patch)
    item_healed=heal.patch(original_item.decode("utf-8"))
    patched_host,patched_item=own.patch_sources(host_original,item_healed)
    # Preserve every author hunk except exactly our one inserted predicate.
    if patched_host.replace(own.HOST_INSERT,"",1)!=host_original:
        raise ValueError("host source regression")
    if patched_item.replace(own.ITEM_INSERT,"",1)!=item_healed:
        raise ValueError("ITEM source regression against original #517 HEAL")
    if item_healed.replace(heal.HELPER,"",1).replace(heal.CALL,"",1)!=original_item.decode("utf-8"):
        raise ValueError("#517 HEAL hunk modifies #489 author elsewhere")
    if output_project.exists() or output_receipt.exists():
        raise ValueError("refuse to replace existing private composite")
    output_project.parent.mkdir(parents=True, exist_ok=True)
    overlay_dir=output_project.parent/"gq525_source_selected_only"
    overlay_dir.mkdir(exist_ok=True)
    host_file=overlay_dir/own.HOST_NAME
    item_file=overlay_dir/own.ITEM_NAME
    for path in (host_file,item_file):
        if path.exists():
            raise ValueError("refuse to overwrite scratch originals")
    host_file.write_text(patched_host,encoding="utf-8")
    item_file.write_text(patched_item,encoding="utf-8")
    data=json.loads(base_project.read_text(encoding="utf-8"))
    data["name"]="EGGRUMBLE_ITEM_MODE_GQ_AUTHOR26_PRIVATE_NOT_RC"
    for name,path in ((HOST,host_file),(ITEM,item_file)):
        data["tree"]["ServerScriptService"][name]["$path"]=os.path.relpath(
            path,output_project.parent).replace(os.sep,"/")
    output_project.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    generated=scripts(output_project)
    if set(generated)!=set(base):
        raise ValueError("source identities changed")
    for name,(_,path) in generated.items():
        if name not in (HOST,ITEM) and sha(path.read_bytes())!=sha(base[name][1].read_bytes()):
            raise ValueError(f"unowned original source changed: {name}")
    receipt.update({
      "status":"GQ525_PRIVATE_AUTHOR26_COMPOSITE_NOT_OFFICIAL_RC",
      "source_changes":[HOST,ITEM],
      "unchanged_original_sources":EXPECTED-2,
      "script_count":EXPECTED,
      "source_sha256":{name:sha(path.read_bytes()) for name,(_,path) in generated.items()},
      "original_source_sha256":{name:sha(path.read_bytes()) for name,(_,path) in base.items()},
      "source_authors":{"game":AUTHOR_482,"composition":AUTHOR_484,
                        "art":AUTHOR_485,"score":AUTHOR_487,
                        "item":AUTHOR_489,"heal":AUTHOR_517},
      "real_engine":"NOT_TESTED","studio":"NOT_TESTED","android":"NOT_TESTED",
      "official_RC_adopted":False,"owner_accepted":False,
      "rollback":"remove these two source-selected overrides; original #484 26-source Place remains",
    })
    output_receipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ525_26_COMPOSITE_24_UNCHANGED_2_OVERLAY_PASS",len(generated))

def check(project: Path, receipt_path: Path, place: Path, compiler: Path) -> None:
    mapped=scripts(project)
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    if set(receipt["source_sha256"])!=set(mapped):
        raise ValueError("receipt names drift")
    expected={}
    for name,(lineage,path) in sorted(mapped.items()):
        if sha(path.read_bytes())!=receipt["source_sha256"][name]:
            raise ValueError(f"source receipt drift {name}")
        cls="Script" if path.name.endswith(".server.luau") else (
            "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        expected[name]=(cls,path.read_text(encoding="utf-8").replace("\r\n","\n"))
        subprocess.run([str(compiler),str(path)],stdout=subprocess.DEVNULL,check=True)
    actual={}
    for node in ET.fromstring(place.read_bytes()).iter("Item"):
        cls=node.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):
            continue
        props=node.find("Properties")
        if props is None:
            continue
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source=props.findtext("string[@name='Source']")
        if name in actual or source is None:
            raise ValueError(f"duplicate/missing source for {name}")
        actual[name]=(cls,source.replace("\r\n","\n"))
    if actual!=expected:
        raise ValueError("Rojo Place source/class not equal to 26 exact original authors + 2 source-selected hunks: "
                         +str({"missing":list(set(expected)-set(actual)),
                               "extra":list(set(actual)-set(expected)),
                               "different":sorted(k for k in set(expected)&set(actual) if expected[k]!=actual[k])}))
    receipt["private_place_bytes"]=place.stat().st_size
    receipt["private_place_sha256"]=sha(place.read_bytes())
    receipt["rojo_source_exact"]="26/26"
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ525_PRIVATE26_NATIVE_ROJO_SOURCE_EXACT_PASS",len(expected),
          receipt["private_place_bytes"],receipt["private_place_sha256"])

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("compose","verify"))
    for arg in ("base_project","base_receipt","item_author","heal_patch","out_project",
                "out_receipt","place","compiler"):
        parser.add_argument("--"+arg.replace("_","-"),type=Path)
    a=parser.parse_args()
    if a.mode=="compose":
        assert all((a.base_project,a.base_receipt,a.item_author,a.heal_patch,a.out_project,a.out_receipt))
        compose(a.base_project,a.base_receipt,a.item_author,a.heal_patch,a.out_project,a.out_receipt)
    else:
        assert all((a.out_project,a.out_receipt,a.place,a.compiler))
        check(a.out_project,a.out_receipt,a.place,a.compiler)
if __name__=="__main__":
    main()
