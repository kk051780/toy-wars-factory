#!/usr/bin/env python3
"""GQ512 exact-current31 one-Replay port of original author #512 policy.
No second gameplay authority. OFF exactly restores prior current RoundReplay.
Original author #512 fixed e232b9a8411879c2c1a945c0a8ed09233ca73fff.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_shield_cleanup_20261117"))
from select_shield import mapping
NAME="EGGRUMBLE_RoundReplay"
ANCHOR=' p:SetAttribute("EGGRUMBLE_NeutralKOs",0)\n'
EXTRA=' p:SetAttribute("EGGRUMBLE_Combo",0)\n p:SetAttribute("EGGRUMBLE_BestCombo",0)\n'
FILE="EGGRUMBLE_RoundReplay_GQ512_COMBO.luau"
RECEIPT="GQ512_COMBO_RC31_RECEIPT.json"
FEATURE="GQ512_ROUND_COMBO_REPLAY_RESET_20261117"
def patch(s):
    if s.count(ANCHOR)!=1 or "function Replay.resetHuman(" not in s: raise ValueError("RED_GQ512_RESET_ANCHOR_OR_OWNER")
    if 'p:SetAttribute("EGGRUMBLE_Combo",' in s or 'p:SetAttribute("EGGRUMBLE_BestCombo",' in s: raise ValueError("RED_GQ512_ALREADY_APPLIED")
    if "GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN" not in s: raise ValueError("RED_GQ512_PARENT_SHIELD_MISSING")
    out=s.replace(ANCHOR,ANCHOR+EXTRA,1)
    assert unpatch(out)==s
    return out
def unpatch(s):
    if s.count(ANCHOR+EXTRA)!=1: raise ValueError("RED_GQ512_ROLLBACK_ANCHOR")
    return s.replace(ANCHOR+EXTRA,ANCHOR,1)
def selftest():
    s='function Replay.resetHuman(p:Player,returnTo:Vector3,baseWalkSpeed:number?):()\n'+ANCHOR+' -- GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN\nend\n'
    assert unpatch(patch(s))==s and patch(s).count(EXTRA)==1
    for broken in (s.replace(ANCHOR,ANCHOR+ANCHOR),s.replace("GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN","BAD"),s.replace("Replay.resetHuman","Other.resetHuman")):
        try:patch(broken)
        except (ValueError,AssertionError):pass
        else: raise ValueError("RED_GQ512_BAD_SOURCE_ACCEPTED")
    try:patch(patch(s))
    except ValueError:pass
    else:raise ValueError("RED_GQ512_DOUBLE_APPLY")
    print("GQ512_SOURCE_LOCK_INVERSE_NEGATIVE_5_PASS")
def prepare(base,out):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or base.parent!=out.parent:raise ValueError("RED_GQ512_OUTPUT_COLLISION")
    obj,files,key=mapping(base)
    before=files[key].read_text(encoding="utf-8");after=patch(before)
    source=out.parent/FILE
    if source.exists():raise ValueError("RED_GQ512_SOURCE_COLLISION")
    source.write_text(after,encoding="utf-8")
    selected=copy.deepcopy(obj);node=selected["tree"]
    for k in key:node=node[k]
    node["$path"]=FILE
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,latest,newkey=mapping(out)
    if key!=newkey or [k for k in files if files[k].read_bytes()!=latest[k].read_bytes()]!=[key]:
        raise ValueError("RED_GQ512_OTHER30_MODIFIED")
    rec={"feature_id":FEATURE,"original_author_pr":512,"original_author_head":"e232b9a8411879c2c1a945c0a8ed09233ca73fff",
         "base":base.name,"selected":out.name,"source_count":31,"changed_script":NAME,
         "other30_exact":True,"off_rollback_exact":True,"new_game_remote_store":0,
         "before_sha256":hashlib.sha256(before.encode()).hexdigest(),
         "after_sha256":hashlib.sha256(after.encode()).hexdigest(),
         "native":"PENDING","rojo":"PENDING","formal_rc":"CANDIDATE_ONLY",
         "studio_android_fun_owner":"NOT_TESTED"}
    (out.parent/RECEIPT).write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GQ512_SELECTED_REAL31_ONE_REPLAY_OTHER30_EXACT")
def harness(project,out,mutant):
    _,files,key=mapping(project)
    source=files[key].read_text(encoding="utf-8")
    if source.count(EXTRA)!=1:raise ValueError("RED_GQ512_NOT_SELECTED")
    begin=source.index("function Replay.resetHuman(")
    stop=source.index(' local stats=p:FindFirstChild("leaderstats")',begin)
    body=source[begin:stop]+"\nend\n"
    head="local Players={}\nlocal Replay={}\n"
    tail="""
local function mk(parent)
 local p={Parent=parent,attrs={EGGRUMBLE_Combo=12,EGGRUMBLE_BestCombo=25,EGGRUMBLE_BossDefeats=9}}
 function p:SetAttribute(k,v) self.attrs[k]=v end
 return p
end
local p=mk(Players)
Replay.resetHuman(p,nil,nil)
assert(p.attrs.EGGRUMBLE_Combo==0,"RED_COMBO_NOT_ZERO")
assert(p.attrs.EGGRUMBLE_BestCombo==0,"RED_BEST_NOT_ZERO")
assert(p.attrs.EGGRUMBLE_BossDefeats==9,"RED_BOSS_OWNER_INTERFERENCE")
local outsider=mk({})
Replay.resetHuman(outsider,nil,nil)
assert(outsider.attrs.EGGRUMBLE_Combo==12,"RED_OUTSIDER_WRITTEN")
assert(outsider.attrs.EGGRUMBLE_BestCombo==25,"RED_OUTSIDER_BEST_WRITTEN")
print("GQ512_REAL_REPLAY_NATIVE_ROUND_LOCAL_5_CASE_PASS")
"""
    out.write_text(head+body+tail,encoding="utf-8")
    mutant.write_text(head+body.replace(' p:SetAttribute("EGGRUMBLE_Combo",0)\n',"",1)+tail,encoding="utf-8")
    print("GQ512_NATIVE_AND_MUTANT_GENERATED")
def verify(base,out,place):
    _,old,key=mapping(base)
    _,latest,newKey=mapping(out)
    if key!=newKey or len(latest)!=31 or set(latest)!=set(old):raise ValueError("RED_GQ512_MAP")
    if patch(old[key].read_text(encoding="utf-8"))!=latest[key].read_text(encoding="utf-8"):raise ValueError("RED_GQ512_CONTENT_DRIFT")
    if [k for k in old if old[k].read_bytes()!=latest[k].read_bytes()]!=[key]:raise ValueError("RED_GQ512_OTHER_SOURCE")
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        klass=item.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_GQ512_XML_PROPS")
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None:src=props.findtext("string[@name='Source']")
        if not name or src is None or name in found:raise ValueError("RED_GQ512_XML_NAMES")
        found[name]=(klass,src.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={k[-1] for k in latest}:raise ValueError("RED_GQ512_XML31")
    for k,path in latest.items():
        klass="Script" if path.name.endswith(".server.luau") else ("LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[k[-1]]!=(klass,path.read_text(encoding="utf-8").replace("\r\n","\n")):raise ValueError("RED_GQ512_ROJO_SOURCE "+k[-1])
    receipt=out.parent/RECEIPT
    d=json.loads(receipt.read_text(encoding="utf-8"))
    d.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,place_sha256=hashlib.sha256(place.read_bytes()).hexdigest())
    receipt.write_text(json.dumps(d,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GQ512_COMBO_SELECTED31_NATIVE_ROJO_SOURCE_OFF_EXACT_PASS")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("command",choices=["selftest","prepare","native","verify"])
    p.add_argument("--base",type=Path);p.add_argument("--out",type=Path);p.add_argument("--project",type=Path);p.add_argument("--mutant",type=Path);p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.command=="selftest":selftest()
    elif a.command=="prepare":prepare(a.base,a.out)
    elif a.command=="native":harness(a.project,a.out,a.mutant)
    else:verify(a.base,a.out,a.place)
