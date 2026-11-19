#!/usr/bin/env python3
"""Run after pinned Native65-67 Luau CLI and Rojo 7.7.1 are already installed.
All 68 actual selected source texts compiled; OFF67 rebuild must be exact.
"""
from __future__ import annotations
import hashlib,json,os,subprocess
from pathlib import Path
root=Path("artifacts/real68")
proj=json.loads((root/"EGGRUMBLE_REAL68.project.json").read_text())
r=json.loads((root/"REAL68_TWIN_INTAKE_RECEIPT.json").read_text())
def selected(tree:dict)->dict[str,str]:
 out={}
 def walk(node,prefix=()):
  for k,v in node.items():
   if k.startswith("$") or not isinstance(v,dict):continue
   route=prefix+(k,)
   if "$path" in v:out["/".join(route)]=v["$path"]
   else:walk(v,route)
 walk(tree)
 return out
paths=selected(proj["tree"])
assert len(paths)==68 and len(set(paths))==68
assert r["selected_source_count"]==68 and r["previous_formal67_count"]==67
assert r["unchanged_existing_sources"]==66
assert r["new_route"]=="ServerScriptService/EGGRUMBLE_LegacyTwinBiomes"
assert r["modified_existing_routes"]==["ServerScriptService/EGGRUMBLE_SevenRoleCombat"]
assert r["new_remotes"]==r["second_game_owners"]==r["new_store_hp_ko_score_writers"]==0
assert r["species_instances_per_arena"]==8
assert r["bond_neutral_basic_max_multiplier"]==1.2
assert r["ported_flags"]==["TWIN_BIOMES_4NPC_V1","TWIN_CREATURE_TRAINING_V1","TWIN_BOND_PVE_COMPANION_V1"]
for route,path in paths.items():
 data=(root/path).read_bytes()
 subprocess.run(["/tmp/gq863-luau/luau-compile","--text",str(root/path)],
                check=True,stdout=subprocess.DEVNULL)
 if route==r["new_route"]:assert hashlib.sha256(data).hexdigest()==r["new_script_sha256"]
 elif route=="ServerScriptService/EGGRUMBLE_SevenRoleCombat":
  assert hashlib.sha256(data).hexdigest()==r["new_combat_sha256"]
 else:assert hashlib.sha256(data).hexdigest()==r["source_fences"][route]["sha256"]
print("GQ8_ORIGINAL_RC85_TWIN_NATIVE_ACTUAL_68_OF_68_NONLOSS_PASS")
subprocess.run(["/tmp/gq863-rojo","build",str(root/"EGGRUMBLE_REAL68.project.json"),
                "-o",str(root/"EGGRUMBLE_REAL68_PRIVATE.rbxlx")],check=True)
subprocess.run(["/tmp/gq863-rojo","build",str(root/"off67/EGGRUMBLE_REAL67.project.json"),
                "-o",str(root/"OFF67_REBUILT.rbxlx")],check=True)
assert (root/"OFF67_REBUILT.rbxlx").read_bytes()==(root/"OFF67_EXACT_ORIGINAL.rbxlx").read_bytes()
assert (root/"OFF67_EXACT_ORIGINAL.rbxlx").read_bytes()==Path("artifacts/real67/EGGRUMBLE_REAL67_PRIVATE.rbxlx").read_bytes()
subprocess.run(["python3","quality_gameplay/gq8_lss_real31_20261117/rehydrate_real31.py",
                "verify","--project",str(root/"EGGRUMBLE_REAL68.project.json"),
                "--place",str(root/"EGGRUMBLE_REAL68_PRIVATE.rbxlx"),"--count","68"],check=True)
place=root/"EGGRUMBLE_REAL68_PRIVATE.rbxlx"
r.update({"candidate_head":os.environ["GITHUB_SHA"],
  "formal_adopted":os.environ["GITHUB_REF"]=="refs/heads/rc/p0d-s1-kids-rc01",
  "private_place_bytes":place.stat().st_size,
  "private_place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
  "native_selected":"PASS_68_OF_68","rojo_source_class":"PASS_68_OF_68",
  "off67_place_byte_exact":True})
(root/"REAL68_TWIN_INTAKE_RECEIPT.json").write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
print("GQ8_TWIN_REAL68_SOURCE_HASH_ROJO68_OFF67_EXACT_PASS",place.stat().st_size)
