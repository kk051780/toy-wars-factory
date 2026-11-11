#!/usr/bin/env python3
"""Native OFFICIAL client HUD + FirstMinuteCoach LocalScript integration replay.

Runs REAL, fixed Git-blob-pinned Luau source with test-only UI/event doubles.
Original script bodies are copied unchanged except Coach Roblox ModuleScript
require binding -> the identically executed original FirstMinuteModel module.
No Roblox Studio, actual GUI rendering, device measurement or network timings.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

RC = "5dc6c958ea5549b1e859d6d250e6179e731181fb"
BASE = "releases/P0D_S1_KIDS_RC01/"
SOURCES = {
    "HUD": ("src/client/HUD.client.luau", "458a23e83d261c51b3bec174e36e183960532f8c"),
    "Coach": ("src/client/FirstMinuteCoach.client.luau", "63f7c013c8523cd628d3d2ffe8da5d08b6adfbd9"),
    "Model": ("src/shared/FirstMinuteModel.luau", "fcdc399bf95b6cd0532691718f5a54e8a4fd84b4"),
}
REPLACE = 'local Model = require(shared:WaitForChild("FirstMinuteModel"))'
F = r'''
-- TEST-ONLY Roblox UI/Remote double. All app logic below is exact original.
local now=0
local function time() return now end
local workspace={}
function workspace:GetServerTimeNow() return now end
local function signal()
 local s={listeners={}}
 function s:Connect(fn)
  table.insert(self.listeners,fn)
  return {Disconnect=function() end}
 end
 function s:Fire(...)
  for _,fn in ipairs(self.listeners) do fn(...) end
 end
 return s
end
local childrenCreated=0
local countRemotesMade=0
local Instance={}
local function newNode(cls)
 local node={ClassName=cls,__type="Instance",children={}}
 node.MouseButton1Click=signal()
 node.Destroying=signal()
 local methods={}
 function methods:WaitForChild(name)
  local x=self.children[name]
  if x==nil then error("NO_FAKE_CHILD_"..name) end
  return x
 end
 function methods:FindFirstChild(name) return self.children[name] end
 function methods:IsA(which) return which==self.ClassName or which=="Instance" end
 function methods:Destroy() self.Destroying:Fire(); self.Destroyed=true end
 setmetatable(node,{
  __index=function(self,k) return methods[k] end,
  __newindex=function(self,k,v)
   rawset(self,k,v)
   if k=="Parent" and v~=nil then
    if v.children==nil then error("INVALID_TEST_PARENT") end
    if type(self.Name)=="string" then
      v.children[self.Name]=self
    end
   end
  end
 })
 return node
end
function Instance.new(cls)
 if cls=="RemoteEvent" then countRemotesMade+=1 end
 childrenCreated+=1
 return newNode(cls)
end
local Color3={
 fromRGB=function(r,g,b) return {r=r,g=g,b=b} end,
 new=function(r,g,b) return {r=r,g=g,b=b} end
}
local Vector2={new=function(x,y) return {x=x,y=y} end}
local UDim={new=function(a,b) return {a,b} end}
local UDim2={
 new=function(...) return {...} end,
 fromOffset=function(...) return {...} end,
 fromScale=function(...) return {...} end
}
local Enum={
 ZIndexBehavior={Sibling="Sibling"},
 Font={GothamBold="GothamBold",Gotham="Gotham"},
 TextXAlignment={Left="Left"},
 TextYAlignment={Top="Top"},
 TextTruncate={AtEnd="AtEnd"},
 KeyCode={F="F",G="G"},
}
local playerGui=newNode("PlayerGui")
playerGui.Name="PlayerGui"
local player={children={PlayerGui=playerGui}}
function player:WaitForChild(name) return self.children[name] end
local Players={LocalPlayer=player}
local input={InputBegan=signal()}
local remote={Name="TrapRaidersS1Remote",OnClientEvent=signal(),sent={}}
function remote:FireServer(payload) table.insert(self.sent,payload) end
local shared={Name="TrapRaidersShared"}
function shared:WaitForChild(name)
 if name~="FirstMinuteModel" then error("UNKNOWN_SHARED_MODULE_"..tostring(name)) end
 return {Name=name}
end
local storage={}
function storage:WaitForChild(name)
 if name=="TrapRaidersS1Remote" then return remote end
 if name=="TrapRaidersShared" then return shared end
 error("UNKNOWN_REPLICATED_CHILD_"..tostring(name))
end
local game={}
function game:GetService(name)
 if name=="Players" then return Players end
 if name=="UserInputService" then return input end
 if name=="ReplicatedStorage" then return storage end
 error("UNKNOWN_SERVICE_"..tostring(name))
end
local function get(root,...) -- strict hierarchy, no guessed Roblox UIs
 local x=root
 for _,name in ipairs({...}) do
  if x.children==nil then error("NO_CHILDREN_"..name) end
  x=x.children[name]
  if x==nil then error("MISSING_UI_INSTANCE_"..name) end
 end
 return x
end
local function snap(phase,serial,team,winner,reason,carry,score,role)
 return {
  kind="SNAPSHOT",phase=phase,serial=serial,time=9,
  scores={RED=score or 0,BLUE=0},hp={RED=300,BLUE=300},
  team=team or "RED",role=role or "RAIDER",
  carrying=carry or "",winner=winner or "",reason=reason or "",
  alarm="IDLE",alarmTime=0,redPlayers=1,bluePlayers=1
 }
end
local function emit(s) remote.OnClientEvent:Fire(s) end
local function check(v,w,name)
 __nativeChecks+=1
 if v~=w then error("REAL_CLIENT_ASSERT_"..name.." actual="..tostring(v).." expected="..tostring(w),0) end
end
local function includes(s,word,name)
 __nativeChecks+=1
 if type(s)~="string" or not string.find(s,word,1,true) then
  error("REAL_CLIENT_ASSERT_"..name.." text="..tostring(s),0)
 end
end
local __nativeChecks=0
'''
# __nativeChecks must be declared before check() closes over it.
F = F.replace("local function check(v,w,name)", "local __nativeChecks=0\nlocal function check(v,w,name)").replace("local __nativeChecks=0\n'''", "'''")
F = F.rsplit("local __nativeChecks=0", 1)[0]  # last declaration removed, keep first
TEST = r'''
local hud=get(playerGui,"TrapRaidersS1HUD")
local score=get(hud,"Score")
local status=get(hud,"Status")
local attack=get(hud,"Attack")
local raider=get(hud,"RaiderRole")
local guardian=get(hud,"GuardianRole")
local coach=get(playerGui,"TR_S1_FirstMinuteCoach")
local panel=get(coach,"CoachPanel")
local title=get(panel,"CoachTitle")
local detail=get(panel,"CoachDetail")
local close=get(panel,"HideHelp")
local show=get(coach,"ShowHelp")
check(#remote.OnClientEvent.listeners,2,"exact_two_local_script_subscribers")
check(#remote.sent,0,"initial_no_client_server_intents")
check(countRemotesMade,0,"no_new_remote")
emit(snap("LOBBY",0,"RED","","","",0))
check(panel.Visible,true,"lobby_coach_visible")
includes(title.Text,"役職","lobby_guide_visible")
includes(status.Text,"2人","lobby_HUD_visible")
raider.MouseButton1Click:Fire()
guardian.MouseButton1Click:Fire()
check(#remote.sent,2,"two_role_intents")
check(remote.sent[1].action,"ROLE","raider_intent")
check(remote.sent[1].role,"RAIDER","raider_selection")
check(remote.sent[2].role,"GUARDIAN","guardian_selection")
check(remote.sent[1].seq,1,"seq1")
check(remote.sent[2].seq,2,"seq2")
now=0
emit(snap("ACTIVE",1,"RED","","","",0))
check(attack.Visible,true,"attack_available_active")
check(guardian.Visible,false,"role_select_hidden_active")
check(panel.Visible,true,"first_minute_panel")
includes(title.Text,"敵のお城","first12_guide")
local sent0=#remote.sent
attack.MouseButton1Click:Fire()
input.InputBegan:Fire({KeyCode=Enum.KeyCode.F},false)
check(#remote.sent,sent0+2,"tap_and_keyboard_intents")
check(remote.sent[sent0+1].action,"ATTACK","tap_attack")
check(remote.sent[sent0+2].action,"ATTACK","keyboard_attack")
check(remote.sent[sent0+1].seq,3,"seq3")
check(remote.sent[sent0+2].seq,4,"seq4")
check(remote.sent[sent0+1].targetId,nil,"no_target_id")
check(remote.sent[sent0+1].damage,nil,"no_client_damage")
check(remote.sent[sent0+1].position,nil,"no_client_position")
input.InputBegan:Fire({KeyCode=Enum.KeyCode.F},true)
check(#remote.sent,sent0+2,"processed_F_must_not_attack")
input.InputBegan:Fire({KeyCode=Enum.KeyCode.G},false)
check(#remote.sent,sent0+2,"wrong_key_must_not_attack")
now=13
emit(snap("ACTIVE",1,"RED","","","",0))
includes(title.Text,"卵を取る","12_to32_prompt")
now=34
emit(snap("ACTIVE",1,"RED","","","",0))
includes(title.Text,"城を攻める","32_to60_prompt")
now=61
emit(snap("ACTIVE",1,"RED","","","",0))
check(panel.Visible,false,"first_minute_auto_hide")
check(show.Visible,true,"help_remains_available")
emit(snap("ACTIVE",1,"RED","","","BLUE",0))
check(panel.Visible,true,"egg_notice_overrides_60sec_auto_hide")
includes(title.Text,"卵をゲット","egg_help")
emit(snap("ACTIVE",1,"RED","","","",1))
includes(title.Text,"得点できた","score_success_guide")
-- Reopening manual help must override later auto hide, not before it.
close.MouseButton1Click:Fire()
check(panel.Visible,false,"close_panel")
check(show.Visible,true,"show_help_icon")
show.MouseButton1Click:Fire()
check(panel.Visible,true,"reopen_panel")
emit(snap("RESULTS",1,"RED","RED","EGG_CAPTURE","",2))
check(attack.Visible,false,"attack_hidden_in_results")
includes(status.Text,"勝利！","localized_win")
includes(status.Text,"卵を運んで得点","localized_capture_reason")
includes(title.Text,"つぎの対戦","coach_rematch")
local staleHud=status.Text
emit(snap("RESULTS",0,"RED","BLUE","CASTLE_DESTROYED","",0))
check(status.Text,staleHud,"reject_stale_HUD_and_coach_snapshot")
emit(snap("RESULTS",2,"RED","BLUE","CASTLE_DESTROYED","",0))
includes(status.Text,"敗北！","localized_loss")
includes(status.Text,"城が破壊された","localized_castle_reason")
emit(snap("RESULTS",3,"RED","DRAW","TIME_LIMIT","",0))
includes(status.Text,"引き分け！","localized_draw")
includes(status.Text,"制限時間が終了","localized_timeout")
emit(snap("RESULTS",4,"RED","BLUE","UNKNOWN_SERVER_REASON","",0))
includes(status.Text,"勝敗が確定しました","unknown_reason_fallback")
if __nativeChecks < 46 then error("REAL_CLIENT_TOO_FEW_ASSERTIONS "..tostring(__nativeChecks),0) end
print("P0D_OFFICIAL_RC_NATIVE_HUD_COACH_CLIENT_PASS assertions="..tostring(__nativeChecks))
'''
# the native test doubles above use ONLY minimal GUI API, no actual device.
MUTATIONS = [
("client_processed_keyboard_guard","HUD",
 'if processed then return end','if false then return end',
 "REAL_CLIENT_ASSERT_processed_F_must_not_attack"),
("client_result_win_copy","HUD",'"勝利！"','"敗北！"',
 "REAL_CLIENT_ASSERT_localized_win"),
("client_no_damage_authority","HUD",
 'remote:FireServer({action = kind, role = role, seq = seq})',
 'remote:FireServer({action = kind, role = role, seq = seq, damage = 999})',
 "REAL_CLIENT_ASSERT_no_client_damage"),
("coach_hide_help","Coach",'Model.setHidden(state, true)','Model.setHidden(state, false)',
 "REAL_CLIENT_ASSERT_close_panel"),
("coach_result_explanation","Model",
 'title = "つぎの対戦も挑戦しよう！"',
 'title = "対戦は終わりました"',
 "REAL_CLIENT_ASSERT_coach_rematch"),
]

def get_original(repo):
    result={}
    for key,(path,blob) in SOURCES.items():
        p=subprocess.run(["git","-C",repo,"show",RC+":"+BASE+path],capture_output=True,check=False)
        if p.returncode:
            raise RuntimeError("MISSING_OFFICIAL_LUAU "+key)
        raw=p.stdout
        sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        if sha!=blob:
            raise RuntimeError("OFFICIAL_UI_SOURCE_CHANGED "+key+" actual="+sha)
        result[key]=raw.decode("utf-8")
    return result

def prepare(modules):
    coach=modules["Coach"]
    if coach.count(REPLACE)!=1:
        raise RuntimeError("ORIGINAL_COACH_MODULE_REQUIRE_ANCHOR_CHANGED")
    coach=coach.replace(REPLACE,"local Model = __real_FirstMinuteModel",1)
    return (F
        +"local __real_FirstMinuteModel=(function()\n"+modules["Model"]+"\nend)()\n"
        +"local function runOriginalHUD()\n"+modules["HUD"]+"\nend\n"
        +"local function runOriginalCoach()\n"+coach+"\nend\n"
        +"runOriginalHUD()\nrunOriginalCoach()\n"
        +TEST)

def run_native(executable,source,path):
    path.write_text(source,encoding="utf-8")
    p=subprocess.run([executable,str(path)],capture_output=True,text=True,check=False,timeout=30)
    return p.returncode,p.stdout+p.stderr

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",required=True)
    ap.add_argument("--luau",required=True)
    args=ap.parse_args()
    modules=get_original(args.repo)
    with TemporaryDirectory(prefix="p0d_client_ui_") as td:
        path=Path(td)/"original_hud_coach.luau"
        rc,output=run_native(args.luau,prepare(modules),path)
        match=re.search(r"P0D_OFFICIAL_RC_NATIVE_HUD_COACH_CLIENT_PASS assertions=(\d+)",output)
        if rc!=0 or not match or int(match.group(1))<46:
            raise RuntimeError("NATIVE_ACTUAL_CLIENT_GUI_FAILED "+output[-2400:])
        print(match.group(0))
        for tag,module,before,after,expect in MUTATIONS:
            s=modules[module]
            if s.count(before)!=1:
                raise RuntimeError("NON_UNIQUE_NEGATIVE_SOURCE_"+tag+" "+str(s.count(before)))
            mutated=dict(modules)
            mutated[module]=s.replace(before,after,1)
            code,out=run_native(args.luau,prepare(mutated),path)
            if code==0 or expect not in out:
                raise RuntimeError("NEGATIVE_CLIENT_MUTATION_UNDETECTED_"+tag+" "+out[-1200:])
            print("P0D_NATIVE_CLIENT_UI_MUTATION_REJECTED "+tag)
        print("P0D_OFFICIAL_RC_NATIVE_CLIENT_NEGATIVE_CONTROLS="+str(len(MUTATIONS)))
    return 0

if __name__ == "__main__":
    try: sys.exit(main())
    except (RuntimeError,OSError,UnicodeError,subprocess.TimeoutExpired) as e:
        print("P0D_NATIVE_CLIENT_UI_BLOCKED "+str(e),file=sys.stderr)
        sys.exit(1)
