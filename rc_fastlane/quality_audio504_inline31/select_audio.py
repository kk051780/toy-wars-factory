#!/usr/bin/env python3
"""GQ504 original author #504: optional real-hit audio inside existing CombatFeel.
All game scripts stay 31. Source lock author, exact inverse, all 30 others byte-identical.
No extra Game/Remote/Store/Damage/HUD or Roblox uploaded sound assets.
"""
from __future__ import annotations
import argparse,copy,hashlib,importlib.util,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_shield_cleanup_20261117"))
from select_shield import mapping

FEATURE="GQ504_ORIGINAL_CONFIRMED_HIT_AUDIO_INLINE_20261117"
AUDIO_BLOB="f2c0e2c811e0a289e9ce9bdf269744d15d21eb7e"
RUNNER_BLOB="383d0e7ae6edff904fe655c42c333862b481189d"
AUTHOR_HEAD="385d3242cbc8d0a3008ee818d8dc30040170fce6"
TARGET=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_CombatFeel")
FILE="GQ504_COMBATFEEL_CONFIRMED_AUDIO.client.luau"
RECEIPT="GQ504_AUDIO_RC31_RECEIPT.json"
BEGIN="\n-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117\ndo\n"
END="end\n-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_END_20261117\n"
HEADER="--!strict\n"

def gitblob(raw:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def source_map(path:Path):
 obj,files,_=mapping(path)
 if TARGET not in files or len(files)!=31 or len({k[-1] for k in files})!=31:
  raise ValueError("RED_GQ504_NOT_ONE_EXISTING_COMBATFEEL_31")
 return obj,files
def authored(path:Path)->str:
 raw=path.read_bytes()
 if gitblob(raw)!=AUDIO_BLOB:raise ValueError("RED_GQ504_ORIGINAL_AUTHOR_SOURCE_CHANGED")
 src=raw.decode("utf-8")
 if not src.startswith(HEADER) or not src.endswith("\n"):raise ValueError("RED_GQ504_AUTHOR_FORMAT")
 for text in (
  'if not RunService:IsStudio() then return end',
  'local GROUP="EGGRUMBLE_GQ_ConfirmedHitAudio"',
  "local MAX_PER_WINDOW=6",
  "local MAX_VOICES=4",
  "local MAX_VOLUME=.30",
  'GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")',
  'GetAttributeChangedSignal("EGGRUMBLE_SFXMuted")',
  'GetAttributeChangedSignal("EGGRUMBLE_Eliminated")',
  "onCharacterRemoving=player.CharacterRemoving:Connect",
  'local function confirmedHit()',
  "local function stopVoices()",
  'if SoundService:FindFirstChild(GROUP) then',
  'if not profile then return end',
 ):
  if src.count(text)!=1:raise ValueError("RED_GQ504_ORIGINAL_AUTHOR_CONTRACT_"+text)
 for bad in ("TakeDamage(","FireServer(","DataStoreService","MarketplaceService","RemoteEvent","SetAttribute("):
  if bad in src:raise ValueError("RED_GQ504_AUTHOR_WRITES_GAME")
 return src[len(HEADER):]
def chunk(body:str)->str:
 return BEGIN+body+END
def check_base(base:str)->None:
 if not base.startswith(HEADER) or not base.endswith("\n"):raise ValueError("RED_GQ504_EXISTING_SOURCE_FORMAT")
 for required in (
  "GQ496_OBJECTIVE_COMPASS_CURRENT31_20261117",
  "GQ503_SEVEN_ROLE_SECONDARY_FX_LOD_20261117",
  'GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")',
  "ConfirmedHit042",
 ):
  if required not in base:raise ValueError("RED_GQ504_PRIOR_OWNER_REGRESSION_"+required)
 if "GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN" in base or "EGGRUMBLE_GQ_ConfirmedHitAudio" in base:
  raise ValueError("RED_GQ504_DUPLICATE_SOUND_OWNER")
def select(base:str,body:str)->str:
 check_base(base)
 result=base+chunk(body)
 if unselect(result,body)!=base:raise ValueError("RED_GQ504_INVERSE_NOT_EXACT")
 return result
def unselect(after:str,body:str)->str:
 piece=chunk(body)
 if after.count(piece)!=1 or not after.endswith(piece):
  raise ValueError("RED_GQ504_OFF_NOT_EXACT")
 return after[:-len(piece)]
def prepare(base:Path,out:Path,author:Path):
 if base.parent!=out.parent or out.exists():raise ValueError("RED_GQ504_OUTPUT_COLLISION")
 obj,files=source_map(base)
 old=files[TARGET].read_text(encoding="utf-8")
 body=authored(author)
 new=select(old,body)
 target=out.parent/FILE
 if target.exists():raise ValueError("RED_GQ504_SOURCE_FILE_COLLISION")
 target.write_text(new,encoding="utf-8")
 selected=copy.deepcopy(obj)
 node=selected["tree"]
 for key in TARGET:node=node[key]
 node["$path"]=FILE
 out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,later=source_map(out)
 changed=[k for k in files if files[k].read_bytes()!=later[k].read_bytes()]
 if changed!=[TARGET] or unselect(new,body)!=old:raise ValueError("RED_GQ504_OTHER30_OR_INVERSE")
 receipt={
  "feature_id":FEATURE,"original_author_pr":504,"original_author_head":AUTHOR_HEAD,
  "original_author_audio_git_blob":AUDIO_BLOB,"existing_source_count":31,
  "changed_source":"EGGRUMBLE_CombatFeel","other30_exact":True,"off_exact":True,
  "new_game_script_count":0,"new_game_remote_store_score":0,
  "source_sha256_before":sha(old.encode()),"source_sha256_after":sha(new.encode()),
  "studio_only":True,"voices_max":4,"max_cues_per_second":6,"volume_cap":0.30,
  "sound_assets":"built-in Roblox local sounds, no uploads",
  "native":"PENDING","rojo":"PENDING","studio_android_fun_owner":"NOT_TESTED"
 }
 (out.parent/RECEIPT).write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print("GQ504_AUTHOR_REAL_AUDIO_ONE_COMBATFEEL_OTHER30_EXACT_OFF_PASS")
def original_runner(path:Path):
 if gitblob(path.read_bytes())!=RUNNER_BLOB:raise ValueError("RED_GQ504_ORIGINAL_NATIVE_HARNESS_CHANGED")
 spec=importlib.util.spec_from_file_location("gq504_author_vm",str(path))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 if "GQ_REAL_AUDIO_NATIVE_VM_PASS" not in module.POSTLUDE:raise ValueError("RED_GQ504_AUTHOR_NATIVE_TESTS")
 return module
def native(project:Path,author:Path,runner:Path,good:Path,mute:Path,rate:Path):
 _,files=source_map(project)
 body=authored(author)
 real=files[TARGET].read_text(encoding="utf-8")
 if real.count(BEGIN)!=1 or real.count(END)!=1:
  raise ValueError("RED_GQ504_AUDIO_BLOCK_MISSING")
 code=real.split(BEGIN,1)[1].split(END,1)[0]
 if code!=body:raise ValueError("RED_GQ504_COMPOSED_AUDIO_NOT_ORIGINAL_AUTHOR")
 original=original_runner(runner)
 def harness(body:str)->str:
  return original.PRELUDE+"\ndo\n"+body+"end\n"+original.POSTLUDE
 good.write_text(harness(code),encoding="utf-8")
 forbidden='player:GetAttribute("EGGRUMBLE_SFXMuted")==true'
 if code.count(forbidden)!=2:raise ValueError("RED_GQ504_MUTE_GUARD_DRIFT")
 mute.write_text(harness(code.replace(forbidden,"false",1)),encoding="utf-8")
 limit="if windowCount>=MAX_PER_WINDOW then return end"
 if code.count(limit)!=1:raise ValueError("RED_GQ504_RATE_GUARD_DRIFT")
 rate.write_text(harness(code.replace(limit,"if false then return end",1)),encoding="utf-8")
 print("GQ504_ORIGINAL_AUTHOR_AUDIO_ACTUAL_SELECTED_VM_PLUS_MUTE_AND_RATE_MUTANTS_READY")
def verify(base:Path,out:Path,place:Path,author:Path):
 _,before=source_map(base);_,after=source_map(out)
 body=authored(author)
 if set(before)!=set(after):raise ValueError("RED_GQ504_MAP")
 for k in before:
  a=before[k].read_bytes();b=after[k].read_bytes()
  if k==TARGET:
   if select(a.decode("utf-8"),body).encode()!=b or unselect(b.decode("utf-8"),body).encode()!=a:
    raise ValueError("RED_GQ504_COMBATFEEL_DIFFERENCE")
  elif a!=b:raise ValueError("RED_GQ504_OTHER30_BYTE_DIFFERENCE")
 entries={}
 for node in ET.parse(place).getroot().iter("Item"):
  kind=node.get("class")
  if kind not in ("Script","LocalScript","ModuleScript"):continue
  prop=node.find("Properties")
  if prop is None:raise ValueError("RED_GQ504_XML_PROPS")
  name=prop.findtext("string[@name='Name']")
  text=prop.findtext("ProtectedString[@name='Source']")
  if text is None:text=prop.findtext("string[@name='Source']")
  if not name or text is None or name in entries:raise ValueError("RED_GQ504_XML_SOURCE_NAMES")
  entries[name]=(kind,text.replace("\r\n","\n"))
 if len(entries)!=31 or set(entries)!={r[-1] for r in after}:raise ValueError("RED_GQ504_XML_31")
 for route,file in after.items():
  kind="Script" if file.name.endswith(".server.luau") else ("LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
  if entries[route[-1]]!=(kind,file.read_text(encoding="utf-8").replace("\r\n","\n")):
   raise ValueError("RED_GQ504_ROJO_SOURCE_CLASS_"+route[-1])
 p=out.parent/RECEIPT
 rec=json.loads(p.read_text(encoding="utf-8"))
 rec.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,
            place_sha256=sha(place.read_bytes()))
 p.write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print("GQ504_AUTHOR_AUDIO_TRUE_31_NATIVE_ROJO_SOURCE_CLASS_PASS",rec["place_bytes"])
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("action",choices=("prepare","native","verify"))
 for a in ("base","out","author","project","runner","good","mute","rate","place"):
  p.add_argument("--"+a,required=(a=="author"),type=Path)
 z=p.parse_args()
 if z.action=="prepare":prepare(z.base,z.out,z.author)
 elif z.action=="native":native(z.project,z.author,z.runner,z.good,z.mute,z.rate)
 else:verify(z.base,z.out,z.place,z.author)
