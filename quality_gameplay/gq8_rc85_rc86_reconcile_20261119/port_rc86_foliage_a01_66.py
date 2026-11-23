#!/usr/bin/env python3
"""Port original RC86 FB016 camera-to-avatar foliage sightline into existing
V3 A01 distance-LOD LocalScript; no second rendering, combat or Remote owner.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROUTE="StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD"
MARK="GQ8_RC86_FB016_FOLIAGE_SIGHTLINE_V3_20261119"
ORIGINAL_RC86_ARTIFACT=14161823401
ORIGINAL_FOLIAGE_SHA256="cf970e804681698a9e9603547bc211c01e633576c50d6b5c8c81c34b84825865"

def must(v,msg):
    if not v: raise ValueError("RED_FB016_A01_"+msg)

def one(s,old,new,tag):
    must(s.count(old)==1,"ANCHOR_"+tag+"_"+str(s.count(old)))
    return s.replace(old,new,1)

def sha(b): return hashlib.sha256(b).hexdigest()

def port(s):
    must(MARK not in s,"NO_DOUBLE_APPLY")
    must('EGGRUMBLE_FlagshipLandscape_VisualOnly=135' in s
         and 'MAX_TRACKED_PARTS=1800' in s
         and 'RunService:IsStudio()' in s,"ORIGINAL_A01_LOD")
    s=one(s,'local RunService=game:GetService("RunService")',
      'local RunService=game:GetService("RunService")\nlocal Players=game:GetService("Players")',"PLAYER")
    s=one(s,'local trackedCount=0',
      '-- '+MARK+'''
-- Original RC86 FB016 local sightline adapted to exclusively A01-owned ART_Canopy.
local MAX_CANOPIES=160
local canopies:{[BasePart]:boolean}={}
local occluded:{[BasePart]:boolean}={}
local canopyCount=0
local trackedCount=0''',"STATE")
    s=one(s,' records[instance]=maxDist\n trackedCount+=1',
      ''' records[instance]=maxDist
 trackedCount+=1
 if instance.Name:sub(1,10)=="ART_Canopy" and canopyCount<MAX_CANOPIES then
  canopies[instance]=true
  canopyCount+=1
 end''',"REGISTER")
    s=one(s,' records[instance]=nil\n hidden[instance]=nil\n trackedCount=math.max(0,trackedCount-1)',
      ''' records[instance]=nil
 hidden[instance]=nil
 occluded[instance]=nil
 if canopies[instance] then canopies[instance]=nil;canopyCount=math.max(0,canopyCount-1) end
 trackedCount=math.max(0,trackedCount-1)''',"REMOVE")
    s=one(s,'workspace.DescendantAdded:Connect(register)\nworkspace.DescendantRemoving:Connect(remove)',
      '''local registered=workspace.DescendantAdded:Connect(register)
local unregistered=workspace.DescendantRemoving:Connect(remove)
local live=true''',"CONNECTIONS")
    s=one(s,' while script.Parent do\n  task.wait(UPDATE_INTERVAL_SECONDS)',
      ''' while script.Parent and live do
  task.wait(UPDATE_INTERVAL_SECONDS)
  if not live then break end''',"STOP")
    s=one(s,'part.LocalTransparencyModifier=if isFar then 1 else 0',
      'part.LocalTransparencyModifier=if isFar then 1 elseif occluded[part] then .93 else 0',"LOD_SINGLE_WRITER")
    extra='''
-- The original S1 FB016 used geometry projection, not client damage/Remote.
-- Budget: at most 160 A01 canopies, sampled every 0.16 seconds.
local function blocksAvatar(p:BasePart,eye:Vector3,avatar:Vector3):boolean
 local delta=avatar-eye
 local len=delta:Dot(delta)
 if len<.01 then return false end
 local t=(p.Position-eye):Dot(delta)/len
 if t<=0 or t>=1 then return false end
 local nearest=eye+delta*t
 local radius=math.max(p.Size.X,p.Size.Y,p.Size.Z)*.5
 return (p.Position-nearest).Magnitude<radius+2.5
end
local fadeTick=0
local fadeConn=RunService.RenderStepped:Connect(function(dt:number)
 if not live or canopyCount==0 then return end
 fadeTick+=math.min(dt,.25)
 if fadeTick<.16 then return end
 fadeTick=0
 local camera=workspace.CurrentCamera
 if not camera then return end
 local eye=camera.CFrame.Position
 local localPlayer=Players.LocalPlayer
 local char=localPlayer and localPlayer.Character
 local root=char and char:FindFirstChild("HumanoidRootPart")
 local avatar:Vector3?=if root and root:IsA("BasePart") then root.Position else nil
 for part in pairs(canopies) do
  if records[part] and part:IsDescendantOf(workspace) and not hidden[part] then
   local radius=math.max(part.Size.X,part.Size.Y,part.Size.Z)*.5
   local nearCamera=(part.Position-eye).Magnitude<radius+9
   local hidesAvatar=if avatar then blocksAvatar(part,eye,avatar) else false
   local fade=nearCamera or hidesAvatar
   if occluded[part]~=fade then
    occluded[part]=fade
    part.LocalTransparencyModifier=if fade then .93 else 0
   end
  else
   -- Original distance-based LOD retains exclusive control of far objects.
   occluded[part]=nil
  end
 end
end)
script.Destroying:Connect(function()
 live=false
 fadeConn:Disconnect()
 registered:Disconnect()
 unregistered:Disconnect()
 for part in pairs(records) do
  if part:IsDescendantOf(workspace) then part.LocalTransparencyModifier=0 end
 end
 table.clear(records)
 table.clear(hidden)
 table.clear(canopies)
 table.clear(occluded)
end)
'''
    s=one(s,'print("[EGGRUMBLE A01 CLIENT LOD]',extra+'\nprint("[EGGRUMBLE A01 CLIENT LOD]',"CAMERA")
    must(s.count(MARK)==1 and s.count('RunService.RenderStepped:Connect')==1,"ONE_CAMERA_LOOP")
    must(s.count('local MAX_TRACKED_PARTS=1800')==1 and s.count('originalA01Distance(')>=2,"PRESERVE_LOD")
    must("RemoteEvent" not in s and "TakeDamage" not in s,"NO_GAME_AUTHORITY")
    return s

def integrate(project_path,receipt_path):
    root=project_path.parent
    project=json.loads(project_path.read_text())
    receipt=json.loads(receipt_path.read_text())
    must(receipt['new_selected_source_count']==65 and len(receipt['sources'])==65,"BASE65")
    rows={r['route']:r for r in receipt['sources']}
    must(len(rows)==65 and ROUTE in rows and rows[ROUTE]['class']=='LocalScript',"SELECTED_LOCAL")
    must(receipt.get('rc85_dojo_lobby_training')
         and receipt.get('legacy_rc86_wind')
         and receipt.get('rc86_three_undead_command')
         and receipt.get('rc86_starry_path'),"PRESERVE_CUMULATIVE_GAME")
    def get(row):
        node=project['tree']
        for seg in row['route'].split('/'): node=node[seg]
        path=root/node['$path']
        content=path.read_bytes()
        must(len(content)==row['bytes'] and sha(content)==row['sha256'],"SOURCE_SHA_"+row['route'])
        return path,content
    for row in receipt['sources']: get(row)
    path,old=get(rows[ROUTE])
    new=port(old.decode('utf-8')).encode('utf-8')
    must(new!=old,"REAL_SOURCE_DELTA")
    path.write_bytes(new)
    rows[ROUTE]['bytes']=len(new)
    rows[ROUTE]['sha256']=sha(new)
    for row in receipt['sources']: get(row)
    receipt['rc86_fb016_foliage_sightline']={
      "feature_id":MARK,
      "original_rc86_artifact_id":ORIGINAL_RC86_ARTIFACT,
      "original_foliage_source_sha256":ORIGINAL_FOLIAGE_SHA256,
      "changed_original_route":ROUTE,
      "unchanged_other_original_routes":64,
      "new_scripts":0,"new_game_remote_damage_store_owners":0,
      "owned_prefix":"ART_Canopy",
      "original_A01_distance_lod_preserved":True,
      "max_canopies":160,"sightline_interval_seconds":0.16,
      "source_class":"LocalScript","studio_private_only":True,
      "original_client_sha256":sha(old),"new_client_sha256":sha(new),
      "native_rojo":"PENDING","studio_visual":"NOT_TESTED",
      "android_15min":"NOT_TESTED","art":"NO_GO","fun":"NO_GO",
      "rollback":"Drop this single A01 LocalScript overlay, keep 66 source build from prior official HEAD"
    }
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ8_FB016_FOLIAGE_A01_SIGHTLINE_65_SOURCE_PLUS_ORIGINAL_66TH_PASS")

def selftest():
    must(one("x","x","y","GOOD")=="y","REPLACE")
    for s in ("none","xx"):
        try: one(s,"x","y","NEGATIVE")
        except ValueError: pass
        else: raise AssertionError("fail-close regression")
    print("GQ8_FB016_A01_FAIL_CLOSED_SELFTEST_PASS")

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--project",type=Path)
    a.add_argument("--receipt",type=Path)
    a.add_argument("--self-test",action="store_true")
    args=a.parse_args()
    if args.self_test: selftest()
    else:
        must(args.project and args.receipt,"ARGS_REQUIRED")
        integrate(args.project,args.receipt)
