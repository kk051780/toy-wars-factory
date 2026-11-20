#!/usr/bin/env python3
"""Compose V3 exact31 + permanent LSS base + realm server/client as core34.
This is a proposed baseline source profile. Does not update RC/main itself.
NO Studio-only gate in the generated core34 traversal; rollback is exact31.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
LSS = HERE.parent / "EGGRUMBLE-LAND-SEA-SKY-20261117" / "EGGRUMBLE_LandSeaSkyTraversal.server.luau"
SERVER = HERE / "EGGRUMBLE_RealmBattleCore.server.luau"
CLIENT = HERE / "EGGRUMBLE_RealmBattleControls.client.luau"
STUDIO_GATE = "if not RunService:IsStudio() then return end"


def get_files(project: Path):
    model = json.loads(project.read_text(encoding="utf-8"))
    result = {}
    def scan(obj, route):
        for key, child in obj.items():
            if key.startswith("$"):
                continue
            if not isinstance(child, dict):
                raise ValueError("RED_BAD_ROJO_CHILD")
            path = route + (key,)
            if "$path" in child:
                src = (project.parent / child["$path"]).resolve(strict=True)
                if path in result: raise ValueError("RED_DUPLICATE_ROUTE")
                result[path] = src
            else:
                scan(child, path)
    scan(model["tree"], ())
    return model, result


def compose(source31: Path, output: Path, off: bool = False, lss_source: Path | None = None):
    source31 = source31.resolve(strict=True)
    output = output.resolve()
    if source31 == output or output.exists():
        raise ValueError("RED_OVERWRITE")
    model, baseline = get_files(source31)
    if len(baseline) != 31:
        raise ValueError("RED_NOT_31")
    names = {path[-1] for path in baseline}
    if not {"EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_SwarmCombat"}.issubset(names):
        raise ValueError("RED_NOT_V3_SESSION")
    addon_names = {"EGGRUMBLE_LandSeaSkyTraversal",
                   "EGGRUMBLE_RealmBattleCore",
                   "EGGRUMBLE_RealmBattleControls"}
    if addon_names & names: raise ValueError("RED_DUPLICATE_SOURCE")
    model = copy.deepcopy(model)
    model["name"] = "EGGRUMBLE_V3_REALM_CORE34" if not off else "EGGRUMBLE_V3_ORIGINAL31"
    output.parent.mkdir(parents=True,exist_ok=True)
    def rebase(node,route=()):
        for key,child in node.items():
            if key.startswith("$"): continue
            here=route+(key,)
            if "$path" in child:
                child["$path"]=os.path.relpath(baseline[here],output.parent).replace(os.sep,"/")
            else: rebase(child,here)
    rebase(model["tree"])
    if not off:
        current_lss = (lss_source or LSS).resolve(strict=True)
        for path in (current_lss,SERVER,CLIENT):
            if not path.is_file(): raise ValueError("RED_MISSING_CORE_SOURCE_"+path.name)
        body=current_lss.read_text(encoding="utf-8")
        if body.count(STUDIO_GATE)!=1: raise ValueError("RED_STUDIO_GATE_CHANGED")
        body=body.replace(STUDIO_GATE,
            "-- Promoted REALM34 core: same V3 session guards on all servers; no Studio gate.")
        promoted=output.parent/"EGGRUMBLE_LandSeaSkyTraversal.Core34.server.luau"
        promoted.write_text(body,encoding="utf-8")
        server=model["tree"].setdefault("ServerScriptService",{})
        server["EGGRUMBLE_LandSeaSkyTraversal"]={
            "$path":os.path.relpath(promoted,output.parent).replace(os.sep,"/")}
        server["EGGRUMBLE_RealmBattleCore"]={
            "$path":os.path.relpath(SERVER,output.parent).replace(os.sep,"/")}
        starter=model["tree"].setdefault("StarterPlayer",{}).setdefault("StarterPlayerScripts",{})
        if "EGGRUMBLE_RealmBattleControls" in starter:
            raise ValueError("RED_DUPLICATE_CLIENT")
        # .client.luau already supplies LocalScript class; Rojo rejects
        # specifying $className twice (project + filesystem).
        starter["EGGRUMBLE_RealmBattleControls"]={
            "$path":os.path.relpath(CLIENT,output.parent).replace(os.sep,"/")}
    output.write_text(json.dumps(model,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _, selected = get_files(output)
    if len(selected)!=(31 if off else 34): raise ValueError("RED_WRONG_SOURCE_COUNT")
    for route,orig in baseline.items():
        if selected.get(route)!=orig or selected[route].read_bytes()!=orig.read_bytes():
            raise ValueError("RED_ORIGINAL31_NOT_BYTE_EXACT")
    receipt={
        "profile":"eggrumble_v3_realm_core34",
        "core_enabled":not off,
        "source_count":len(selected),
        "original_31_byte_exact":True,
        "original_31_sha256":{"/".join(k):hashlib.sha256(p.read_bytes()).hexdigest()
                              for k,p in baseline.items()},
        "added_source_names":sorted(addon_names) if not off else [],
        "legacy_rich51_unmodified":True,
        "main_modified":False,
        "studio_android_owner_tested":False,
        "publication_authorized":False,
        "requires": ["native34","rojo34_source_class","inverse31","Studio_2client",
                     "Android15m","Combat_Host_api_for_human_vehicle_damage"]
    }
    output.with_suffix(".receipt.json").write_text(
        json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ8_CORE_OFF31_BYTE_EXACT" if off else "GQ8_REALM_BASE34_SOURCE_EXACT")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--current31",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--off",action="store_true")
    parser.add_argument("--lss-source",type=Path,
        help="Exact LSS file from current official RC SHA; do not use stale PR checkout")
    a=parser.parse_args()
    compose(a.current31,a.out,a.off,a.lss_source)
