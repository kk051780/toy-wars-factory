#!/usr/bin/env python3
"""GQ506: source-pin original R13 death-ticket respawn protection on existing Host31.

Existing single LobbyCastleModesPreview server Script remains the only host.
Other30 real source bytes exact, complete OFF inverse, true Native/Rojo31.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_castle_prompt_session_20261117"))
from select_castle import mapping

FEATURE="GQ506_RESPAWN_GRACE_SINGLE_HOST_20261117"
AUTHOR_SHA="cab48cb5db058442fb4135084b81a57b0bac78c4"
AUTHOR_BLOB="862d5e8811e744e74eda5893128ea4a88267c3a4"
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
NAME="GQ506_RESPAWN_HOST31.server.luau"
RECEIPT="GQ506_RESPAWN_RC31_RECEIPT.json"
MARK="GQ506_RESPAWN_GRACE_SINGLE_HOST_20261117"
PRE="\ndo -- "+MARK+": immutable original R13 ServerScript in single existing Host\n"
END="\nend\n"

def blob(raw:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def orig(path:Path)->str:
 raw=path.resolve(strict=True).read_bytes()
 if blob(raw)!=AUTHOR_BLOB:raise ValueError("RED_GQ506_ORIGINAL_SOURCE_BLOB")
 src=raw.decode("utf-8")
 if not src.startswith("--!strict\n") or not src.endswith("\n"):
  raise ValueError("RED_GQ506_AUTHOR_HEADER")
 for item in (
  "local GRACE_SECONDS = 2.25",
  "local RESPAWN_TICKET_SECONDS = 12",
  "local MAX_HOME_DISTANCE = 85",
  "local function currentArena(player: Player, character: Model)",
  "local function originArena(player: Player, character: Model)",
  "local function install(player: Player, character: Model)",
  "humanoid.Died:Connect(function()",
  "tickets[player] = {",
  "tickets[player] = nil",
  "if not ticket or os.clock() > ticket.expiresAt then return end",
  "currentArena(player, character) ~= ticket.arena",
  "player:GetAttribute(\"EGGRUMBLE_QueuedMode\") ~= ticket.mode",
  "ProximityPromptService.PromptTriggered:Connect",
  'Instance.new("ForceField")',
  "if instance:IsA(\"Tool\") then revoke() end",
  "if state.shield.Parent then state.shield:Destroy() end",
  "if not RunService:IsStudio() then return end"
 ):
  if item not in src:raise ValueError("RED_GQ506_AUTHOR_SECURITY_ANCHOR "+item)
 for item in ("FireServer(","InvokeServer(","DataStore","MarketplaceService","TakeDamage(","Rules.damageCastle("):
  if item in src:raise ValueError("RED_GQ506_DUPLICATE_AUTHORITY "+item)
 return src

def addition(auth:str)->str:
 return PRE+auth.removeprefix("--!strict\n")+END

def patch(before:str,auth:str)->str:
 if not before.startswith("--!strict\n") or not before.endswith("\n"):
  raise ValueError("RED_GQ506_HOST_FORMAT")
 for guard in (
  'local Players=game:GetService("Players")',
  'EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW',
  '-- GQ8_HUMAN_SIEGE_PACING_BEGIN',
  'or session.isCurrentHuman(p)~=true then return end',
  'session.isCurrentHuman'
 ):
  if guard not in before:raise ValueError("RED_GQ506_EXISTING_HOST_GUARD_LOST "+guard)
 if MARK in before or 'EGGRUMBLE_GQ_RespawnGrace' in before:
  raise ValueError("RED_GQ506_ALREADY_PRESENT_DUPLICATE")
 new=before+addition(auth)
 if unpatch(new,auth)!=before:raise ValueError("RED_GQ506_OFF_NOT_EXACT")
 return new

def unpatch(after:str,auth:str)->str:
 a=addition(auth)
 if after.count(a)!=1 or not after.endswith(a):raise ValueError("RED_GQ506_OFF_SCOPE_DRIFT")
 return after[:-len(a)]

def inspect(base:Path,out:Path,auth:str):
 _,old=mapping(base);_,new=mapping(out)
 if len(old)!=len(new) or len(old)!=31 or set(old)!=set(new) or HOST not in old:
  raise ValueError("RED_GQ506_SOURCE_COUNT_OWNER")
 diff=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
 if diff!=[HOST]:raise ValueError("RED_GQ506_CHANGED_OTHER30 "+str(diff))
 a=old[HOST].read_text(encoding="utf-8")
 b=new[HOST].read_text(encoding="utf-8")
 if patch(a,auth)!=b or unpatch(b,auth)!=a:
  raise ValueError("RED_GQ506_SELECTED_SOURCE_NOT_INVERSIBLE")
 if not new[HOST].name.endswith(".server.luau"):
  raise ValueError("RED_GQ506_NOT_SERVER_SCRIPT")
 return a,b,new

def prepare(base:Path,out:Path,author:Path):
 base=base.resolve(strict=True);out=out.resolve()
 auth=orig(author)
 project,files=mapping(base)
 before=files[HOST].read_text(encoding="utf-8")
 after=patch(before,auth)
 selected=out.parent/NAME; receipt=out.parent/RECEIPT
 if out.exists() or selected.exists() or receipt.exists() or out.parent!=base.parent:
  raise ValueError("RED_GQ506_OUTPUT_COLLISION")
 selected.write_text(after,encoding="utf-8")
 chosen=copy.deepcopy(project)
 chosen["tree"][HOST[0]][HOST[1]]["$path"]=NAME
 out.write_text(json.dumps(chosen,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 inspect(base,out,auth)
 receipt.write_text(json.dumps({
  "feature_id":FEATURE,"author_pr":506,"author_head":AUTHOR_SHA,
  "author_script_blob":AUTHOR_BLOB,"source_count":31,
  "changed_existing_script":HOST[-1],"unchanged_other30_bytes":True,
  "off_exact":True,"new_script_count":0,"new_remote_game_datastore":0,
  "requires_genuine_death_ticket":True,"single_use_ticket_seconds":12,
  "max_grace_seconds":2.25,"home_distance_studs":85,
  "source_before_sha256":sha(before.encode()),"source_after_sha256":sha(after.encode()),
  "native":"PENDING","rojo":"PENDING",
  "studio_2client_android15_fun_owner":"NOT_TESTED","public_publish":False
 },indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("GQ506_ORIGINAL_RESPAWN_GRACE_SINGLE_HOST_31_OTHER30_EXACT_OFF_PASS")

def verify(base:Path,out:Path,author:Path,place:Path):
 before,after,files=inspect(base.resolve(strict=True),out.resolve(strict=True),orig(author))
 actual={}
 for it in ET.parse(place).getroot().iter("Item"):
  kind=it.get("class")
  if kind not in ("Script","LocalScript","ModuleScript"):continue
  props=it.find("Properties")
  if props is None:raise ValueError("RED_GQ506_ROJO_PROPERTIES")
  name=props.findtext("string[@name='Name']")
  src=props.findtext("ProtectedString[@name='Source']")
  if src is None:src=props.findtext("string[@name='Source']")
  if not name or src is None or name in actual:raise ValueError("RED_GQ506_ROJO_DUPLICATE")
  actual[name]=(kind,src.replace("\r\n","\n"))
 if len(actual)!=31 or set(actual)!={k[-1] for k in files}:
  raise ValueError("RED_GQ506_ROJO31_NOT_REAL")
 for route,src in files.items():
  kind="Script" if src.name.endswith(".server.luau") else (
   "LocalScript" if src.name.endswith(".client.luau") else "ModuleScript")
  if actual[route[-1]]!=(kind,src.read_text(encoding="utf-8").replace("\r\n","\n")):
   raise ValueError("RED_GQ506_ROJO_SOURCE_CLASS_"+route[-1])
 receipt=out.parent/RECEIPT
 rec=json.loads(receipt.read_text(encoding="utf-8"))
 if rec["source_before_sha256"]!=sha(before.encode()) or rec["source_after_sha256"]!=sha(after.encode()):
  raise ValueError("RED_GQ506_RECEIPT_HASH")
 rec.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,place_sha256=sha(place.read_bytes()))
 receipt.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("GQ506_NATIVE31_ROJO31_EXACT_ORIGINAL_RESPAWN_DEATH_TICKET_PASS")

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("command",choices=["prepare","verify"])
 p.add_argument("--base",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--author",type=Path,required=True)
 p.add_argument("--place",type=Path)
 a=p.parse_args()
 if a.command=="prepare":prepare(a.base,a.out,a.author)
 else:
  if a.place is None:p.error("verify needs place")
  verify(a.base,a.out,a.author,a.place)
