#!/usr/bin/env python3
"""Execute the REAL audio LocalScript in a minimal fake Roblox Luau runtime.

No gameplay replica: assert only local audio behavior and preexisting server events.
"""
import argparse
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "EGGRUMBLE_RealHitAudio.client.luau"
PRELUDE = r'''
local fakeTime=0
local plays={}
local objects={}
local function signal()
 local s={listeners={}}
 function s:Connect(fn)
  local conn={active=true}
  conn:Disconnect=function(self) self.active=false end
  table.insert(self.listeners,{conn=conn,fn=fn})
  return conn
 end
 function s:Fire(...)
  for _,item in ipairs(self.listeners) do
   if item.conn.active then item.fn(...) end
  end
 end
 return s
end
local Instance={}
function Instance.new(className)
 local obj={ClassName=className,Parent=nil,playCount=0,stopCount=0,playing=false}
 function obj:FindFirstChild(name)
  for _,v in ipairs(objects) do
   if v.Parent==self and v.Name==name then return v end
  end
  return nil
 end
 function obj:Play()
  self.playCount+=1
  self.playing=true
  table.insert(plays,{id=self.SoundId,speed=self.PlaybackSpeed,vol=self.Volume})
 end
 function obj:Stop()
  self.stopCount+=1
  self.playing=false
 end
 function obj:Destroy()
  self.Parent=nil
 end
 table.insert(objects,obj)
 return obj
end
local soundService=Instance.new("SoundService")
local humanoid={Health=100}
local character={}
function character:FindFirstChildOfClass(name)
 if name=="Humanoid" then return humanoid end
 return nil
end
local attributes={}
local signals={}
local player={Character=character,AncestryChanged=signal()}
function player:GetAttribute(key)
 return attributes[key]
end
function player:GetAttributeChangedSignal(key)
 if not signals[key] then signals[key]=signal() end
 return signals[key]
end
local services={
 Players={LocalPlayer=player},
 RunService={IsStudio=function(_) return true end},
 SoundService=soundService,
}
local game={}
function game:GetService(name)
 return services[name]
end
local os={clock=function() return fakeTime end}
local function warn(_msg) end
'''
POSTLUDE = r'''
local checks=0
local function check(p,msg)
 checks+=1
 assert(p,msg)
end
local function send(sequence,role,slot,weight)
 attributes.EGGRUMBLE_ImpactRole=role
 attributes.EGGRUMBLE_ImpactSlot=slot
 attributes.EGGRUMBLE_ImpactWeight=weight
 attributes.EGGRUMBLE_ImpactSequence=sequence
 signals.EGGRUMBLE_ImpactSequence:Fire()
end
local function attr(name,value)
 attributes[name]=value
 if signals[name] then signals[name]:Fire() end
end
local function allSilent()
 for _,sound in ipairs(objects) do
  if sound.ClassName=="Sound" and sound.playing then return false end
 end
 return true
end
local folder=soundService:FindFirstChild("EGGRUMBLE_GQ_ConfirmedHitAudio")
check(folder~=nil,"sound service folder created")
local voices=0
for _,object in ipairs(objects) do
 if object.ClassName=="Sound" then voices+=1 end
end
check(voices==4,"bounded sound pool")
check(#plays==0,"never play on initialization/miss")
fakeTime=0
send(1,"WARRIOR","A",1)
check(#plays==1,"actual server hit should play")
check(plays[1].id:find("action_jump_land",1,true)~=nil,"warrior profile")
check(plays[1].vol<=.30,"bounded volume")
send(1,"WARRIOR","A",1)
check(#plays==1,"duplicate impact sequence rejected")
fakeTime=.22
send(0,"WARRIOR","A",1)
check(#plays==1,"stale reset sequence rejected")
send(2,"MAGE","B",3)
check(#plays==2,"newer confirmed hit plays")
check(plays[2].id~=plays[1].id,"class character sound differs")
check(plays[2].speed>1,"skill pitch profile")
attr("EGGRUMBLE_SFXMuted",true)
check(allSilent(),"mute immediately silences playing voices")
fakeTime=.50
send(3,"NINJA","C",3)
check(#plays==2,"muted cannot play")
attr("EGGRUMBLE_SFXMuted",false)
check(#plays==2,"unmute never synthesizes a hit")
fakeTime=.70
send(4,"NINJA","C",3)
check(#plays==3,"unmuted actual hit can play")
attr("EGGRUMBLE_Eliminated",true)
check(allSilent(),"elimination immediately silences all voices")
fakeTime=.95
send(5,"BEAST","A",1)
check(#plays==3,"eliminated caster silent")
attr("EGGRUMBLE_Eliminated",false)
humanoid.Health=0
fakeTime=1.2
send(6,"BEAST","A",1)
check(#plays==3,"dead humanoid silent")
humanoid.Health=100
fakeTime=1.5
send(7,"NOT_A_ROLE","A",1)
check(#plays==3,"unknown role fail closed")
fakeTime=5.0
local before=#plays
for i=1,7 do
 send(7+i,"BUILDER","A",1)
 fakeTime+=.15
end
check(#plays-before==6,"max six cues per rolling second")
check(#plays>3,"native loop executed")
fakeTime=6.3
send(15,"ZOMBIE","C",2)
check(#plays-before==7,"second window recovered")
check(plays[#plays].vol<=.30,"all roles volume cap")
player.AncestryChanged:Fire(player,nil)
check(allSilent(),"leaving destroys current sound playback")
check(folder.Parent==nil,"leaving removes optional audio group")
local n=#plays
fakeTime=7
send(16,"MAGE","A",1)
check(#plays==n,"signal cleanup disables future plays")
print("GQ_REAL_AUDIO_NATIVE_VM_PASS",checks,"runtime behavior checks")
'''
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    source = SOURCE.read_text(encoding="utf-8")
    if "local onMute=" not in source or "local onEliminated=" not in source:
        raise ValueError("audio source no longer has expected mute/KO wiring")
    # Execute the actual source as a block. Roblox objects are only minimal stubs.
    args.out.write_text(PRELUDE + "\ndo\n" + source + "\nend\n" + POSTLUDE, encoding="utf-8")

if __name__ == "__main__":
    main()
