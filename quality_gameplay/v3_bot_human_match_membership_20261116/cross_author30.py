#!/usr/bin/env python3
"""ONE source-selective GQ531 overlay on original GQ517 real 30-source composer.

Never alters the original #482/#484/#485/#487/#489/#512/#514/#517
files or protected RC. Selects current #484 Host and #484 BotActors,
not original #482 host (which would discard #484's castle ramp).
The other twenty-eight already-composed owners' sources are unchanged.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

from compose import compose as membership_patch, git_blob_sha, OWNER_HEAD, AI_AUTHOR_HEAD

HOST="EGGRUMBLE_LobbyCastleModesPreview"
BOT="EGGRUMBLE_BotActors"
EXPECTED_484_BLOBS = {
 BOT:"832a26c9f713012b924234ce4cf8c1654a75654e",
}
ORIGINAL_482_HOST_BLOB="7162b209bf67b74a71553217f3f744e072a0365d"
ORIGINAL_484_HOST_BLOB="c1ff23cd2883401d44d6fc47311bebcfd53eb1c6"
EXPECTED_FIRST30_NAMES={HOST,BOT,"EGGRUMBLE_FieldItemPickups","EGGRUMBLE_SevenRoleCombat",
"EGGRUMBLE_CastleMatchRules","EGGRUMBLE_NeutralStoneGiant",
"EGGRUMBLE_RoundAttributeFence","EGGRUMBLE_BossCreditPolicy",
"EGGRUMBLE_MatchResultService"}
SCHEME="GQ531_ON_ORIGINAL_GQ517_30_AUTHOR_SOURCE_20261116"

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def mapped(project:Path):
 doc=json.loads(project.read_text(encoding="utf-8"))
 result={}
 nodes={}
 def walk(node,chain=()):
  if not isinstance(node,dict):return
  if "$path" in node:
   assert set(node)=={"$path"},("RED: mixed Rojo authority",chain)
   assert chain[0] in {"ServerScriptService","StarterPlayer"},chain
   name=chain[-1]
   assert name not in result,("RED: duplicate mapped script",name)
   rel=node["$path"]
   assert isinstance(rel,str) and rel.endswith(".luau")
   source=(project.parent/rel).resolve(strict=True)
   cls="Script" if source.name.endswith(".server.luau") else ("LocalScript" if source.name.endswith(".client.luau") else "ModuleScript")
   result[name]={"source":source,"sha256":sha(source.read_bytes()),"class":cls,"route":chain}
   nodes[name]=node
  else:
   for k,v in node.items():
    if not k.startswith("$"):walk(v,chain+(k,))
 walk(doc["tree"])
 return doc,result,nodes


def verify_host_lineage(base_host:Path, original_host:Path, ai_host:Path, ai_composer:Path):
 original=original_host.read_bytes()
 current=ai_host.read_bytes()
 assert git_blob_sha(original)==ORIGINAL_482_HOST_BLOB,"RED: #482 pinned Host drift"
 assert git_blob_sha(current)==ORIGINAL_484_HOST_BLOB,"RED: #484 pinned castle ramp source drift"
 spec=importlib.util.spec_from_file_location("pinned_author_484_compose",ai_composer)
 assert spec and spec.loader
 module=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(module)
 expected=module.apply_ramp(original.decode("utf-8"),current.decode("utf-8"))
 assert base_host.read_text(encoding="utf-8")==expected, "RED: generated #482 Host + #484 castle ramp source drift"
 assert expected.count("CastleAccessRamp")>=1 and expected.count("session.isCurrentHuman")==0
 return sha(expected.encode("utf-8"))

def prepare(base:Path,out:Path,receipt:Path,original_host:Path,ai_host:Path,ai_composer:Path):
 assert base.resolve()!=out.resolve(),"RED: may not overwrite author composite"
 assert base.parent.resolve()==out.parent.resolve(),"RED: project relocation would break exact source paths"
 doc,original,nodes=mapped(base)
 assert len(original)==30 and EXPECTED_FIRST30_NAMES.issubset(original),("RED: 30-source author composite drift",len(original))
 for name,blob in EXPECTED_484_BLOBS.items():
  observed=git_blob_sha(original[name]["source"].read_bytes())
  if observed!=blob:
   raise AssertionError(f"RED: #484 original {name} drift: {observed} != {blob}")
 generated_host_sha=verify_host_lineage(original[HOST]["source"],original_host,ai_host,ai_composer)
 assert original[HOST]["class"]=="Script" and original[BOT]["class"]=="ModuleScript"
 assert [x for x in original.values() if x["route"][-1]==HOST][0]["route"]==("ServerScriptService",HOST)
 assert not any("isCurrentHuman" in original[name]["source"].read_text(encoding="utf-8") for name in [HOST,BOT])
 host_raw=original[HOST]["source"].read_text(encoding="utf-8")
 bot_raw=original[BOT]["source"].read_text(encoding="utf-8")
 host,bot=membership_patch(host_raw,bot_raw)
 if host.replace("  -- Authoritative host-only membership fence for BotActors hero hits.\n"
     "  -- Never trust a stale castle ID or a client-side teleport as proof of participation.\n"
     '  session.isCurrentHuman=function(player:Player):boolean\n'
     '   return sessions[mode]==session and session.rules.phase=="ACTIVE"\n'
     '    and joined[player.UserId]==mode and player.Parent==Players\n'
     '    and session.rules.castles[tostring(player.UserId)]~=nil\n'
     '    and session.rules.castles[tostring(player.UserId)].isAI~=true\n'
     '  end\n', "",1)!=host_raw:
  raise AssertionError("RED: Host overlay not exactly one callback")
 assert bot.count("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)")==1
 assert bot.count("for targetId,targetActor in pairs(bots)")==1
 overlay={HOST:("GQ531_AuthorCurrentHost.server.luau",host),BOT:("GQ531_AuthorCurrentBot.luau",bot)}
 for name,(filename,source) in overlay.items():
  target=out.parent/filename
  assert target.resolve()!=original[name]["source"].resolve(),"RED: would overwrite author"
  target.write_text(source,encoding="utf-8")
  nodes[name]["$path"]=filename
 doc["name"]="GQ531_ORIGINAL8DOMAINS_30_NO_OFFICIAL_RC"
 out.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 _,selection,_=mapped(out)
 assert set(selection)==set(original) and len(selection)==30
 changed={n for n in original if selection[n]["sha256"]!=original[n]["sha256"]}
 assert changed=={HOST,BOT},("RED: changed another author",changed)
 for n in set(original)-changed:
  assert selection[n]==original[n],("RED: author source mapping drift",n)
 lock={
  "mode":SCHEME,
  "candidate_head":os.environ.get("GITHUB_SHA","LOCAL_ONLY"),
  "source_owners":{"game":"#482 "+OWNER_HEAD,"spatial_and_bot":"#484 "+AI_AUTHOR_HEAD,
   "art":"#485 e86702c906bdf9c71adcdf769ae48a206b26607b",
   "score":"#487 438a406ccfda5563053d783d7561797ccd364361",
   "item":"#489 03c51bf5c8d12484bd8dc4667b0d3d3841cb4ddd",
   "heal":"#517 c8a324ad7bb40648d82a5828cbf54e217585fefd",
   "combo":"#512 e232b9a8411879c2c1a945c0a8ed09233ca73fff",
   "boss":"#514 0d1be13be6d895bea460ba54aaa91ef346684d7f"},
  "base_project_sha256":sha(base.read_bytes()),
  "selected_source_hashes":{n:selection[n]["sha256"] for n in sorted(selection)},
  "unchanged_owners":{n:original[n]["sha256"] for n in sorted(set(original)-changed)},
  "prior_host_bot":{
   HOST:{"source_lineage":"#482 original Host exact blob + #484 castle ramp exact author generator","sha256":generated_host_sha},
   BOT:{"git_blob":EXPECTED_484_BLOBS[BOT],"sha256":original[BOT]["sha256"]}},
  "changed_source_names":sorted(changed),
  "source_total":30,"private_build":True,"official_rc_adopted":False,
  "real_studio":"NOT_TESTED","android":"NOT_TESTED","art_fun":"NO_GO","owner_accepted":False,
 }
 receipt.write_text(json.dumps(lock,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
 print("GQ531_PRIVATE30_PATCH_ONLY_2_OF_30_PASS",len(set(selection)-changed),len(changed))

def verify(base:Path,out:Path,receipt:Path,place:Path,original_host:Path,ai_host:Path,ai_composer:Path):
 lock=json.loads(receipt.read_text(encoding="utf-8"))
 assert lock["mode"]==SCHEME and lock["official_rc_adopted"] is False
 assert lock["base_project_sha256"]==sha(base.read_bytes()),"RED: base project changed"
 _,original,_=mapped(base)
 _,mapped_out,_=mapped(out)
 assert len(original)==len(mapped_out)==30 and set(original)==set(mapped_out)
 assert lock["changed_source_names"]==sorted([HOST,BOT])
 assert lock["selected_source_hashes"]=={n:mapped_out[n]["sha256"] for n in sorted(mapped_out)}
 assert set(lock["unchanged_owners"])==set(original)-{HOST,BOT}
 for n,expected in lock["unchanged_owners"].items():
  assert original[n]==mapped_out[n] and mapped_out[n]["sha256"]==expected,("RED: another author mutated",n)
 assert verify_host_lineage(original[HOST]["source"],original_host,ai_host,ai_composer)==lock["prior_host_bot"][HOST]["sha256"]
 for n,blob in EXPECTED_484_BLOBS.items():
  assert git_blob_sha(original[n]["source"].read_bytes())==blob
  assert original[n]["source"]!=mapped_out[n]["source"]
 assert original[HOST]["source"]!=mapped_out[HOST]["source"]
 assert mapped_out[HOST]["class"]=="Script" and mapped_out[BOT]["class"]=="ModuleScript"
 assert mapped_out[HOST]["source"].read_text().count("session.isCurrentHuman=function")==1
 assert mapped_out[BOT]["source"].read_text().count("session.isCurrentHuman(player)")==1
 expected={n:(v["class"],v["source"].read_text(encoding="utf-8").replace("\r\n","\n")) for n,v in mapped_out.items()}
 actual={}
 for item in ET.parse(place).iter("Item"):
  cls=item.attrib.get("class")
  if cls not in {"Script","ModuleScript","LocalScript"}:continue
  props=item.find("Properties")
  if props is None:continue
  name=props.findtext("string[@name='Name']")
  assert name and name not in actual,("RED: duplicate embedded script",name)
  source=props.findtext("ProtectedString[@name='Source']")
  if source is None:source=props.findtext("string[@name='Source']")
  assert source is not None,("RED: missing embedded Script Source",name)
  actual[name]=(cls,source.replace("\r\n","\n"))
 assert expected==actual,("RED: Rojo binary Source/Class != 30-script manifest",list(set(expected)^set(actual)))
 lock["private_place_bytes"]=place.stat().st_size
 lock["private_place_sha256"]=sha(place.read_bytes())
 lock["real_rojo_source_exact"]="30/30"
 lock["only_2_changed_from_owner_composite"]=True
 receipt.write_text(json.dumps(lock,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
 print("GQ531_8DOMAIN_30_ROJO_NATIVE_SOURCE_EXACT_PASS",lock["private_place_bytes"],lock["private_place_sha256"])

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("mode",choices=["prepare","verify"])
 p.add_argument("--base",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--receipt",type=Path,required=True)
 p.add_argument("--place",type=Path)
 p.add_argument("--original-host",type=Path,required=True)
 p.add_argument("--ai-host",type=Path,required=True)
 p.add_argument("--ai-composer",type=Path,required=True)
 a=p.parse_args()
 if a.mode=="prepare":prepare(a.base,a.out,a.receipt,a.original_host,a.ai_host,a.ai_composer)
 else:
  if not a.place:p.error("--place is required")
  verify(a.base,a.out,a.receipt,a.place,a.original_host,a.ai_host,a.ai_composer)
