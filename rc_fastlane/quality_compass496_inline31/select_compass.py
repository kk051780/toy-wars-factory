#!/usr/bin/env python3
"""GQ496: original-author FB003/FB014 objective compass inline in existing CombatFeel.

Exactly one client source changes; 30 other gameplay sources identical; no extra
LocalScript, Remote, Game, physics, score, or input authority. Strict OFF.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_castle_prompt_session_20261117"))
from select_castle import mapping

FEATURE="GQ496_OBJECTIVE_COMPASS_CURRENT31_20261117"
AUTHOR_SHA="8434485c4bbe65f03dc310f4b85157fdd6012465"
AUTHOR_BLOB="43feb1c3c55b727c0d5a8fad5195a32d54da18e2"
TARGET=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_CombatFeel")
FILENAME="GQ496_COMBATFEEL_COMPASS.client.luau"
RECEIPT="GQ496_OBJECTIVE_COMPASS_RC31_RECEIPT.json"
MARKER="GQ496_OBJECTIVE_COMPASS_CURRENT31_20261117"
PREFACE="\ndo -- "+MARKER+": ORIGINAL authored #496 independent client kept verbatim\n"
END="\nend\n"

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def original(path:Path):
    raw=path.resolve(strict=True).read_bytes()
    if blob(raw)!=AUTHOR_BLOB:raise ValueError("RED_GQ496_ORIGINAL_AUTHOR_SOURCE_BLOB")
    src=raw.decode("utf-8")
    if not src.startswith("--!strict\n") or not src.endswith("\n"):
        raise ValueError("RED_GQ496_AUTHOR_LUAU_HEADER")
    for marker in (
        'if not RunService:IsStudio() then return end',
        'gui.Name="EGGRUMBLE_GQ_ObjectiveCompass"',
        'local function isEnemy(',
        'local function pickObjective(',
        'local function nearestActiveItem(',
        'if homeSelected then',
        'EGGRUMBLE_QueuedMode',
        'EGGRUMBLE_FieldItems',
        'NEUTRAL_BOSS_STONE_GIANT',
        'if mode~="TEAM" then return false end',
        'INITIAL_SECONDS = 18',
        'UPDATE_SECONDS = 0.8',
        'UserInputService.InputBegan:Connect',
        'RunService.Heartbeat:Connect',
        'marker.AlwaysOnTop=false',
    ):
        if src.count(marker)!=1:raise ValueError("RED_GQ496_SOURCE_BEHAVIOR_DRIFT "+marker)
    for forbidden in ("FireServer(","InvokeServer(","TakeDamage(","DataStore","MarketplaceService"):
        if forbidden in src:raise ValueError("RED_GQ496_CLIENT_AUTHORITY "+forbidden)
    return src

def addition(src:str)->str:
    # Keep literal original authored body intact, including all local functions.
    return PREFACE+src.removeprefix("--!strict\n")+END

def patch(current:str,author:str)->str:
    if not current.startswith("--!strict\n") or not current.endswith("\n"):
        raise ValueError("RED_GQ496_CLIENT_BASE_FORMAT")
    for anchor in (
        'local Players=game:GetService("Players")',
        'local RunService=game:GetService("RunService")',
        'local player=Players.LocalPlayer',
        'if not RunService:IsStudio() then return end',
        'ConfirmedHit042',
        'GQ503_SEVEN_ROLE_SECONDARY_FX_LOD_20261117',
        'local fxSecondaryNames={',
    ):
        if anchor not in current:raise ValueError("RED_GQ496_CURRENT_CLIENT_PREV_FX_HIT_LOST "+anchor)
    if MARKER in current or 'EGGRUMBLE_GQ_ObjectiveCompass' in current:
        raise ValueError("RED_GQ496_COMPASS_ALREADY_PRESENT_NO_DUPLICATE")
    result=current+addition(author)
    if unpatch(result,author)!=current:
        raise ValueError("RED_GQ496_INVERSE")
    return result

def unpatch(current:str,author:str)->str:
    add=addition(author)
    if current.count(add)!=1 or not current.endswith(add):
        raise ValueError("RED_GQ496_ROLLBACK_NOT_EXACT")
    return current[:-len(add)]

def inspect(base:Path,out:Path,auth:str):
    _,old=mapping(base)
    _,new=mapping(out)
    if len(old)!=len(new) or len(old)!=31 or set(old)!=set(new) or TARGET not in old:
        raise ValueError("RED_GQ496_NOT_EXACT31_OWNER")
    changes=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
    if changes!=[TARGET]:raise ValueError("RED_GQ496_OTHER30_GAME_SCRIPT_CHANGED")
    before=old[TARGET].read_text(encoding="utf-8")
    after=new[TARGET].read_text(encoding="utf-8")
    if patch(before,auth)!=after or unpatch(after,auth)!=before:
        raise ValueError("RED_GQ496_ON_OFF_NOT_INVERTIBLE")
    if not new[TARGET].name.endswith(".client.luau"):raise ValueError("RED_GQ496_NOT_CLIENT")
    return before,after,new

def prepare(base:Path,out:Path,authpath:Path):
    base=base.resolve(strict=True)
    out=out.resolve()
    auth=original(authpath)
    project,files=mapping(base)
    before=files[TARGET].read_text(encoding="utf-8")
    after=patch(before,auth)
    selected=out.parent/FILENAME
    receipt=out.parent/RECEIPT
    if out.exists() or selected.exists() or receipt.exists() or out.parent!=base.parent:
        raise ValueError("RED_GQ496_OUTPUT_COLLISION")
    selected.write_text(after,encoding="utf-8")
    newproj=copy.deepcopy(project)
    newproj["tree"][TARGET[0]][TARGET[1]][TARGET[2]]["$path"]=FILENAME
    out.write_text(json.dumps(newproj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    inspect(base,out,auth)
    receipt.write_text(json.dumps({
        "feature_id":FEATURE,"original_pr":496,"original_author_head":AUTHOR_SHA,
        "original_author_git_blob":AUTHOR_BLOB,"game_sources":31,
        "existing_client_script":TARGET[-1],"client_only":True,
        "other30_byte_exact":True,"off_exact":True,"added_runtime_scripts":0,
        "no_game_remote_score":True,"gated_studio_only":True,
        "refresh_cadence_sec":0.8,"auto_collapse_sec":18,
        "source_original_sha256":digest(before.encode()),"source_selected_sha256":digest(after.encode()),
        "native":"PENDING","rojo":"PENDING",
        "studio_android_fun_owner":"NOT_TESTED"
    },sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GQ496_AUTHOR_CLIENT_INLINE_ONE_COMBATFEEL_OTHER30_EXACT_OFF_PASS")

def verify(base:Path,out:Path,authpath:Path,place:Path):
    before,after,selected=inspect(base.resolve(strict=True),out.resolve(strict=True),original(authpath))
    actual={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        prop=item.find("Properties")
        if prop is None:raise ValueError("RED_GQ496_SCRIPT_PROPS")
        name=prop.findtext("string[@name='Name']")
        src=prop.findtext("ProtectedString[@name='Source']")
        if src is None:src=prop.findtext("string[@name='Source']")
        if not name or src is None or name in actual:raise ValueError("RED_GQ496_ROJO_NAME_DUP")
        actual[name]=(cls,src.replace("\r\n","\n"))
    if len(actual)!=31 or set(actual)!={k[-1] for k in selected}:
        raise ValueError("RED_GQ496_NOT_REAL_ROJO31")
    for route,f in selected.items():
        cls="Script" if f.name.endswith(".server.luau") else (
            "LocalScript" if f.name.endswith(".client.luau") else "ModuleScript")
        if actual[route[-1]]!=(cls,f.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_GQ496_ROJO_SOURCE_CLASS_"+route[-1])
    path=out.parent/RECEIPT
    rec=json.loads(path.read_text(encoding="utf-8"))
    if rec["source_original_sha256"]!=digest(before.encode()) or rec["source_selected_sha256"]!=digest(after.encode()):
        raise ValueError("RED_GQ496_SOURCE_RECEIPT_DRIFT")
    rec.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,place_sha256=digest(place.read_bytes()))
    path.write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GQ496_OBJECTIVE_GUI_TRUE_ROJO31_CLIENT_CLASS_OTHER30_BYTE_EXACT",rec["place_bytes"])

def cli():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("prepare","verify"))
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--author",type=Path,required=True)
    p.add_argument("--place",type=Path)
    args=p.parse_args()
    if args.command=="prepare":prepare(args.base,args.out,args.author)
    else:
        if args.place is None:p.error("--place is required")
        verify(args.base,args.out,args.author,args.place)
if __name__=="__main__":cli()
