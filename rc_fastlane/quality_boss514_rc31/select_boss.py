#!/usr/bin/env python3
"""Integrate original #514 BOSS round attribution into existing V3 RoundReplay.
No second listener, score authority or extra runtime Luau Script. Exact inverse.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"quality_shield_cleanup_20261117"))
from select_shield import mapping
MODULE="EGGRUMBLE_RoundReplay"
AUTHOR_PR=514
AUTHOR_HEAD="0d1be13be6d895bea460ba54aaa91ef346684d7f"
FEATURE="GQ514_BOSS_CREDIT_MATCH_RESET_20261117"
ANCHOR=' p:SetAttribute("EGGRUMBLE_BestCombo",0)\n'
INSERT=' p:SetAttribute("EGGRUMBLE_BossDefeats",0)\n'
SELECTED="EGGRUMBLE_RoundReplay_GQ514_BOSS.luau"
RECEIPT="GQ514_BOSS_RC31_RECEIPT.json"

def patch(s:str)->str:
    if s.count("function Replay.resetHuman(")!=1 or s.count(ANCHOR)!=1:
        raise ValueError("RED_GQ514_ORIGINAL_REPLAY_OWNER_OR_ANCHOR")
    if s.count(' p:SetAttribute("EGGRUMBLE_Combo",0)\n')!=1 or "GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN" not in s:
        raise ValueError("RED_GQ514_PREVIOUS_COMBO_SHIELD_LOST")
    if 'p:SetAttribute("EGGRUMBLE_BossDefeats",' in s:
        raise ValueError("RED_GQ514_ALREADY_APPLIED")
    result=s.replace(ANCHOR,ANCHOR+INSERT,1)
    if unpatch(result)!=s:
        raise ValueError("RED_GQ514_INVERSE_NOT_EXACT")
    return result

def unpatch(s:str)->str:
    if s.count(ANCHOR+INSERT)!=1:
        raise ValueError("RED_GQ514_INVERSE_ANCHOR")
    return s.replace(ANCHOR+INSERT,ANCHOR,1)

def selftest():
    valid=('function Replay.resetHuman(p:Player,returnTo:Vector3,baseWalkSpeed:number?):()\n'
           ' p:SetAttribute("EGGRUMBLE_Combo",0)\n'+ANCHOR+
           ' -- GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN\nend\n')
    assert unpatch(patch(valid))==valid
    for broken in (valid.replace(ANCHOR,""),
                   valid.replace(ANCHOR,ANCHOR+ANCHOR),
                   valid.replace("GQ8_MULTI_SHIELD_REPLAY_CLEANUP_BEGIN","BROKEN"),
                   valid.replace("Replay.resetHuman","Fake.resetHuman"),
                   valid.replace(' p:SetAttribute("EGGRUMBLE_Combo",0)\n',"")):
        try:patch(broken)
        except ValueError:pass
        else:raise ValueError("RED_GQ514_NEGATIVE_SOURCE_ACCEPTED")
    try:patch(patch(valid))
    except ValueError:pass
    else:raise ValueError("RED_GQ514_DOUBLE_PATCH_ACCEPTED")
    print("GQ514_SOURCE_NEGATIVES_INVERSE_6_PASS")

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out.parent!=base.parent:
        raise ValueError("RED_GQ514_COLLISION_OR_DIFFERENT_DIR")
    obj,files,key=mapping(base)
    before=files[key].read_text(encoding="utf-8")
    after=patch(before)
    output=out.parent/SELECTED
    if output.exists():raise ValueError("RED_GQ514_EXISTING_SOURCE")
    output.write_text(after,encoding="utf-8")
    candidate=copy.deepcopy(obj)
    leaf=candidate["tree"]
    for segment in key:leaf=leaf[segment]
    leaf["$path"]=SELECTED
    out.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,newFiles,newKey=mapping(out)
    changed=[route for route in files if files[route].read_bytes()!=newFiles[route].read_bytes()]
    if len(newFiles)!=31 or key!=newKey or changed!=[key]:
        raise ValueError("RED_GQ514_OTHER30_CHANGED")
    receipt={
      "feature_id":FEATURE,"original_author_pr":AUTHOR_PR,"original_author_head":AUTHOR_HEAD,
      "base_project":base.name,"selected_project":out.name,"source_count":31,
      "only_changed_script":MODULE,"other30_source_byte_exact":True,
      "off_source_inverse_exact":unpatch(after)==before,"runtime_script_delta":0,
      "new_game_remote_score_store":0,
      "before_sha256":hashlib.sha256(before.encode()).hexdigest(),
      "after_sha256":hashlib.sha256(after.encode()).hexdigest(),
      "native":"PENDING","rojo":"PENDING","studio_engine":"NOT_TESTED",
      "android_15min":"NOT_TESTED","owner_fun":"NO_GO",
      "official_rc_source_adopted":False}
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ514_BOSS_31_SELECTED_ONE_REPLAY_OTHER30_EXACT_OFF_PASS")

def native(project:Path,out:Path,mutant:Path):
    _,files,key=mapping(project)
    text=files[key].read_text(encoding="utf-8")
    if text.count(ANCHOR+INSERT)!=1:raise ValueError("RED_GQ514_NOT_CURRENT_SELECTED")
    begin=text.index("function Replay.resetHuman(")
    end=text.index(' local stats=p:FindFirstChild("leaderstats")',begin)
    body=text[begin:end]+"\nend\n"
    header="local Players={}\nlocal Replay={}\n"
    trailer=StringTail
    out.write_text(header+body+trailer,encoding="utf-8")
    mutant.write_text(header+body.replace(INSERT,"",1)+trailer,encoding="utf-8")
    print("GQ514_REAL_REPLAY_VM_BOSS_AND_MUTANT_PREPARED")

StringTail = """
local function player(parent)
 local p={Parent=parent,attrs={
  EGGRUMBLE_Combo=13,EGGRUMBLE_BestCombo=19,EGGRUMBLE_BossDefeats=8,
  EGGRUMBLE_Unrelated=27}}
 function p:SetAttribute(k,v) self.attrs[k]=v end
 return p
end
local p=player(Players)
Replay.resetHuman(p,nil,nil)
assert(p.attrs.EGGRUMBLE_BossDefeats==0,"RED_GQ514_BOSS_REPLAY_NOT_ZERO")
assert(p.attrs.EGGRUMBLE_Combo==0 and p.attrs.EGGRUMBLE_BestCombo==0,
       "RED_GQ514_PREVIOUS_COMBO_LOST")
assert(p.attrs.EGGRUMBLE_Unrelated==27,"RED_GQ514_UNRELATED_CHANGED")
local outsider=player({})
Replay.resetHuman(outsider,nil,nil)
assert(outsider.attrs.EGGRUMBLE_BossDefeats==8,"RED_GQ514_OUTSIDER_RESET")
assert(outsider.attrs.EGGRUMBLE_Combo==13,"RED_GQ514_OUTSIDER_COMBO")
print("GQ514_REAL_REPLAY_NATIVE_BOSS_ROUND_6_CASE_PASS")
"""

def verify(base:Path,out:Path,place:Path):
    _,old,key=mapping(base)
    _,new,newKey=mapping(out)
    if len(new)!=31 or set(old)!=set(new) or key!=newKey:
        raise ValueError("RED_GQ514_PROJECT_ROUTE_DRIFT")
    before=old[key].read_text(encoding="utf-8")
    after=new[key].read_text(encoding="utf-8")
    if patch(before)!=after or unpatch(after)!=before:
        raise ValueError("RED_GQ514_CONTENT_OR_ROLLBACK")
    if [route for route in old if old[route].read_bytes()!=new[route].read_bytes()]!=[key]:
        raise ValueError("RED_GQ514_OTHER30_DRIFT")
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        clazz=item.get("class")
        if clazz not in ("Script","LocalScript","ModuleScript"):continue
        prop=item.find("Properties")
        if prop is None:raise ValueError("RED_GQ514_PLACE_PROPERTIES")
        name=prop.findtext("string[@name='Name']")
        code=prop.findtext("ProtectedString[@name='Source']")
        if code is None:code=prop.findtext("string[@name='Source']")
        if not name or code is None or name in found:
            raise ValueError("RED_GQ514_PLACE_NAMES")
        found[name]=(clazz,code.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={k[-1] for k in new}:
        raise ValueError("RED_GQ514_ROJO_SOURCE_COUNT")
    for route,path in new.items():
        expected=("Script" if path.name.endswith(".server.luau") else
                  "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]]!=(expected,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_GQ514_ROJO_SOURCE_CLASS_"+route[-1])
    p=out.parent/RECEIPT
    receipt=json.loads(p.read_text(encoding="utf-8"))
    receipt.update(native="31/31",rojo="31/31",
                   place_bytes=place.stat().st_size,
                   place_sha256=hashlib.sha256(place.read_bytes()).hexdigest())
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ514_BOSS_ROUND_FINAL31_NATIVE_ROJO_OFF_EXACT_PASS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("operation",choices=("selftest","prepare","native","verify"))
    for arg in ("base","out","project","mutant","place"):
        a.add_argument("--"+arg,type=Path)
    p=a.parse_args()
    if p.operation=="selftest":selftest()
    elif p.operation=="prepare":prepare(p.base,p.out)
    elif p.operation=="native":native(p.project,p.out,p.mutant)
    else:verify(p.base,p.out,p.place)
if __name__=="__main__":main()
