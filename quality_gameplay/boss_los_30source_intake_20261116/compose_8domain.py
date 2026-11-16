#!/usr/bin/env python3
"""SELECT ONLY original #518 boss + #520 ridge + #523 egg into #517's 30-source private Place.

This script authors ZERO new gameplay Luau. It imports the original owners' source
transform functions at immutable refs, enforces a two-existing-script change budget,
verifies every other source, and records private Rojo / Luau evidence only.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from intake import mapped, sha, git_blob, BOSS_NAME, BOSS_BLOB

HOST="EGGRUMBLE_LobbyCastleModesPreview"
HOST_BLOB="7162b209bf67b74a71553217f3f744e072a0365d"
EXPECTED=30

def import_original(path: Path, name: str):
    path=path.resolve(strict=True)
    # Original #520 imports patch_ridge from its own folder; original #523
    # imports patch_field_eggs via the same convention. Do not copy authors.
    sys.path.insert(0,str(path.parent))
    try:
        spec=importlib.util.spec_from_file_location(name,path)
        assert spec is not None and spec.loader is not None
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)

def prepare(base:Path, base_receipt:Path, author_host:Path, quality_host:Path,
            raid_item:Path, quality_composer:Path, ridge_composer:Path,
            ridge_patch:Path, egg_patch:Path, outdir:Path):
    base=base.resolve(strict=True)
    outdir=outdir.resolve()
    assert outdir!=base.parent and not base.is_relative_to(outdir)
    doc, origin=mapped(base)
    assert len(origin)==EXPECTED and set((HOST,BOSS_NAME,"EGGRUMBLE_SevenRoleCombat",
             "EGGRUMBLE_FieldItemPickups","EGGRUMBLE_RoundAttributeFence",
             "EGGRUMBLE_BossCreditPolicy","EGGRUMBLE_ScoreBalance",
             "EGGRUMBLE_BotActors","EGGRUMBLE_CastleMatchRules")).issubset(origin)
    assert origin[HOST][0]==("ServerScriptService",HOST) and origin[HOST][2]=="Script"
    assert origin[BOSS_NAME][2]=="ModuleScript"
    prior=json.loads(base_receipt.read_text(encoding="utf-8"))
    assert prior["selected_source_count"]==EXPECTED
    assert prior["changed_existing_source_only"]==[BOSS_NAME]
    assert prior["source_exact_sha256"]=={k:sha(v[1].read_bytes()) for k,v in origin.items()}
    # The original author blob must remain *exact* or this private candidate stops.
    raw_author=author_host.resolve(strict=True).read_bytes()
    assert git_blob(raw_author)==HOST_BLOB,"source drift: original #482 Game host changed"
    author=raw_author.decode("utf-8")
    quality=quality_host.resolve(strict=True).read_text(encoding="utf-8")
    item=raid_item.resolve(strict=True).read_text(encoding="utf-8")
    original_host=origin[HOST][1].read_text(encoding="utf-8")
    assert "CastleAccessRamp" in original_host,"#484 castle ramp lost"
    quality_mod=import_original(quality_composer,"original484_composer_for_521")
    ridge_mod=import_original(ridge_composer,"original520_composer_for_521")
    patch_mod=import_original(ridge_patch,"original520_patch_for_521")
    egg_mod=import_original(egg_patch,"original523_patch_for_521")
    assert patch_mod.ORIGINAL_GIT_BLOB==HOST_BLOB
    assert egg_mod.ORIGINAL_HOST_BLOB==HOST_BLOB
    # Reuse the authors' exact operations, not restate/recode their fixes.
    ridge=ridge_mod.patch_composed_host(
        original_host,author,quality,item,
        lambda source,quality_source:quality_mod.apply_ramp(source,quality_source))
    assert ridge!=original_host
    assert ridge.count(patch_mod.NEW)==1 and original_host.count(patch_mod.OLD)==1
    assert ridge.replace(patch_mod.NEW,patch_mod.OLD,1)==original_host
    combined=egg_mod.patch(ridge)
    assert combined!=ridge
    assert combined.replace(egg_mod.ROWS_LINE,"",1).replace(
        egg_mod.REPLACEMENT_LINE,egg_mod.ORIGINAL_LINE,1)==ridge
    assert combined.count("CastleAccessRamp")==original_host.count("CastleAccessRamp")
    assert combined.count("CentralRidgeRight")==ridge.count("CentralRidgeRight")
    assert 'local eggId="FIELD_"..i' in combined
    assert combined.count("for i=1,24 do")==1
    assert "stompVisible" not in combined and "shockwaveClear" not in combined
    # BOSS author source is already selected once in #521; no second patch.
    boss_raw=origin[BOSS_NAME][1].read_bytes()
    assert "shockwaveClear" in boss_raw.decode("utf-8")
    assert boss_raw.count(b"h:TakeDamage(28)")==1
    outdir.mkdir(parents=True,exist_ok=True)
    gen=outdir/"EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    gen.write_text(combined,encoding="utf-8")
    new=copy.deepcopy(doc)
    for name,(path,src,_) in origin.items():
        node=new["tree"]
        for part in path:node=node[part]
        chosen=gen if name==HOST else src
        node["$path"]=Path(os.path.relpath(chosen,outdir)).as_posix()
    new["name"]="EGGRUMBLE_GQ521_SOURCE_SELECTED_ORIGINAL518_520_523_PRIVATE30"
    output=outdir/"GQ521_ORIGINAL_BOSS_FIELD_EGGS_RIDGE30.project.json"
    output.write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _,selected=mapped(output)
    assert len(selected)==EXPECTED and set(selected)==set(origin)
    changes=[]
    for name in sorted(origin):
        a,b=origin[name],selected[name]
        assert a[0]==b[0] and a[2]==b[2],"runtime script place/class drift"
        if a[1].read_bytes()!=b[1].read_bytes():
            changes.append(name)
    assert changes==[HOST],"only one extra host changes vs already selected #518 30"
    assert sha(selected[BOSS_NAME][1].read_bytes())==sha(boss_raw)
    assert sum(x[2]=="Script" for x in origin.values())==sum(x[2]=="Script" for x in selected.values())
    assert sum(x[2]=="LocalScript" for x in origin.values())==sum(x[2]=="LocalScript" for x in selected.values())
    record={
        "status":"PRIVATE_SINGLE_GAME_30_SOURCE_SELECT_AUTHORS_518_520_523_NOT_RC",
        "owners":{"boss_518":"f31081d5cb2bea86d01c76c53bb60cd2f9a8355d",
          "ridge_520":"f53162f4dc1d0f1832942a28bf89df7114ae4f3d",
          "field_egg_523":"7447761aee570f54d57d125e79d21c9cb05bc889"},
        "base_original30_before_extra_host":EXPECTED,
        "selected_source_count":EXPECTED,
        "source_changes_from_original30":[HOST],
        "cumulative_changes_from_unpatched_author30":[HOST,BOSS_NAME],
        "unchanged_scripts_from_selected_boss30":29,
        "unchanged_scripts_from_original_boss_and_host30":28,
        "selected_source_sha256":{k:sha(v[1].read_bytes()) for k,v in selected.items()},
        "original30_source_sha256":{k:sha(v[1].read_bytes()) for k,v in origin.items()},
        "same_boss_sha256":sha(boss_raw),
        "field_ridge_reversible":True,
        "original_484_castle_ramp":True,"field_egg_count_unchanged":24,
        "official_rc_adopted":0,"claim_granted":False,
        "studio":"NOT_RUN","android":"NOT_RUN","owner_accepted":False,
        "known_red":"Original #482 GAME and #512 COMBO Studio-only; live game unverified"}
    receipt=outdir/"GQ521_ORIGINAL8DOMAIN30_RECEIPT.json"
    receipt.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ521_THREE_AUTHORS_SINGLE30_SELECT_PASS 28/30 original untouched, #518 boss+one #520/#523 host")
    return output

def verify(project:Path,place:Path):
    _,selected=mapped(project)
    receipt=project.parent/"GQ521_ORIGINAL8DOMAIN30_RECEIPT.json"
    record=json.loads(receipt.read_text(encoding="utf-8"))
    assert len(selected)==EXPECTED and record["unchanged_scripts_from_original_boss_and_host30"]==28
    assert set(selected)==set(record["selected_source_sha256"])
    observed={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        assert props is not None
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        assert name and source is not None and name not in observed,"missing/duplicate source"
        observed[name]=(cls,source.replace("\r\n","\n"))
    assert set(observed)==set(selected)
    for name,(_,src,cls) in selected.items():
        assert observed[name]==(cls,src.read_text(encoding="utf-8").replace("\r\n","\n"))
        assert sha(src.read_bytes())==record["selected_source_sha256"][name],"readback hash drift"
    record["rojo_source_class_exact"]="30/30"
    record["private_place_bytes"]=place.stat().st_size
    record["private_place_sha256"]=sha(place.read_bytes())
    record["official_rc_adopted"]=0
    receipt.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ521_ORIGINAL_518_520_523_PRIVATE30_REAL_ROJO_EXACT_PASS 30/30",
          record["private_place_bytes"],record["private_place_sha256"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["prepare","verify"])
    for key in ("base","base-receipt","author-host","quality-host","raid-item","quality-composer",
                "ridge-composer","ridge-patch","egg-patch","outdir","project","place"):
        ap.add_argument("--"+key,type=Path)
    a=ap.parse_args()
    if a.mode=="prepare":
        keys=("base","base_receipt","author_host","quality_host","raid_item","quality_composer",
              "ridge_composer","ridge_patch","egg_patch","outdir")
        assert all(getattr(a,key) for key in keys)
        prepare(*(getattr(a,key) for key in keys))
    else:
        assert a.project and a.place
        verify(a.project,a.place)

if __name__=="__main__":
    main()
