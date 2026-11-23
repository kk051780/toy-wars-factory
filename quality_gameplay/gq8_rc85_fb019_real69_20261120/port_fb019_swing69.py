#!/usr/bin/env python3
"""Port old RC85/RC86 FB019 immediate ATTACK feedback to the sole V3 HUD; no damage owner."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

ROUTE="StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime"
OLD_SHA="d24ddcc3ff2942e3b0fecb75ce9554804d6479aee6b9ac0fee3ec5f9379101fc"
MARKER="GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120"
ANCHOR='''actions.ATTACK.Activated:Connect(function()
 closeDrawer()
 activate(basicTool() or slotTool("A"))
end)'''
PATCH='''-- GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120
-- Old RC86 FB019: instant cosmetic feedback, never claims a server-confirmed hit.
local fb019Tween=game:GetService("TweenService")
local fb019Debris=game:GetService("Debris")
local fb019Last=-math.huge
local function fb019VisualSwing()
 if not mapSnapshot or not gui.Enabled or not actions.ATTACK.Visible then return end
 local character=player.Character
 local root=character and character:FindFirstChild("HumanoidRootPart")
 local humanoid=character and character:FindFirstChildOfClass("Humanoid")
 if not root or not root:IsA("BasePart") or not humanoid or humanoid.Health<=0 then return end
 local now=os.clock()
 if now-fb019Last<0.85 then return end
 fb019Last=now
 local basis=root.CFrame
 for index=1,2 do
  local side=if index==1 then -1 else 1
  local slash=Instance.new("Part")
  slash.Name="EGGRUMBLE_FB019_LocalSwing_"..tostring(index)
  slash.Anchored=true
  slash.CanCollide=false
  slash.CanTouch=false
  slash.CanQuery=false
  slash.CastShadow=false
  slash.Material=Enum.Material.Neon
  slash.Color=if index==1 then Color3.fromRGB(255,227,157) else Color3.fromRGB(150,220,255)
  slash.Size=Vector3.new(3.1,.15,.1)
  slash.Transparency=.12
  slash.CFrame=basis*CFrame.new(side*.27,.75,-2.8)*CFrame.Angles(0,0,math.rad(side*32))
  slash.Parent=workspace
  fb019Tween:Create(slash,TweenInfo.new(.18,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),{
   CFrame=basis*CFrame.new(side*.36,1,-4.2)*CFrame.Angles(0,0,math.rad(side*69)),
   Transparency=1,Size=Vector3.new(4,.06,.08)
  }):Play()
  fb019Debris:AddItem(slash,.24)
 end
end
actions.ATTACK.Activated:Connect(function()
 closeDrawer()
 local tool=basicTool() or slotTool("A")
 if tool then
  fb019VisualSwing()
  activate(tool)
 end
end)'''
def need(ok,name):
 if not ok: raise ValueError("RED_FB019_REAL69_"+name)
def selftest():
 need(PATCH.count(MARKER)==1 and PATCH.count('Instance.new("Part")')==1,"SOURCE_SHAPE")
 need('activate(tool)' in PATCH and 'if tool then' in PATCH,"SERVER_TOOL_RETAINED")
 need('fb019Debris:AddItem(slash,.24)' in PATCH and 'now-fb019Last<0.85' in PATCH,"PARTS_BOUNDED")
 for forbidden in ('FireServer(', 'DataStoreService', 'TakeDamage(', 'MarketplaceService','Instance.new("RemoteEvent")'):
  need(forbidden not in PATCH,"FORBIDDEN_AUTHORITY")
 print("GQ8_FB019_REAL69_SOURCE_SELFTEST_PASS")
def run(root,head):
 project="EGGRUMBLE_REAL69.project.json"
 receiptname="REAL69_LEGACY_INTAKE_RECEIPT.json"
 before=project_scan(root,project)
 need(len(before)==69 and ROUTE in before,"69_SELECTED_ROUTE")
 need(before[ROUTE]["sha256"]==OLD_SHA and before[ROUTE]["class"]=="LocalScript","EXPECTED_EXACT_HUD_PARENT")
 receipt=json.loads((root/receiptname).read_text())
 need(receipt.get("selected_source_count")==69 and len(receipt.get("source_hashes",{}))==69,"RECEIPT_COUNT")
 need(all(receipt["source_hashes"].get(k)==v["sha256"] for k,v in before.items()),"RECEIPT_HASHES")
 need("rc85_realm_hunt_discovery_toast" in receipt and "rc85_rc86_fb019_local_swing" not in receipt,"DISCOVERY_NOT_PRESERVED")
 path=root/before[ROUTE]["path"]
 original=path.read_bytes()
 need(original.count(ANCHOR.encode())==1 and MARKER.encode() not in original,"ORIGINAL_ATTACK_BINDING_DRIFT")
 need(not (root/"off69_fb019").exists(),"ROLLBACK_OVERWRITE")
 place=root/"EGGRUMBLE_REAL69_PRIVATE.rbxlx"
 need(place.is_file(),"PARENT_STUDIO_PLACE_MISSING")
 off=root/"off69_fb019"
 shutil.copytree(root/"sources",off/"sources")
 shutil.copy2(root/project,off/project)
 shutil.copy2(root/receiptname,off/receiptname)
 shutil.copy2(place,root/"OFF69_PRE_FB019_EXACT.rbxlx")
 path.write_bytes(original.replace(ANCHOR.encode(),PATCH.encode()))
 after=project_scan(root,project)
 need(len(after)==69 and set(after)==set(before),"ROUTE_69_NONLOSS")
 need(all(before[k]["class"]==after[k]["class"] and before[k]["path"]==after[k]["path"] for k in before),"PATH_CLASS_NONLOSS")
 need([k for k in before if before[k]["sha256"]!=after[k]["sha256"]]==[ROUTE],"ONLY_ONE_SELECTED_HUD_CHANGED")
 receipt["source_hashes"][ROUTE]=after[ROUTE]["sha256"]
 receipt["build_head"]=head
 receipt["rc85_rc86_fb019_local_swing"]={
  "feature_id":MARKER,
  "legacy_flag":"FB019_RESPONSIVE_ATTACK_INPUT_SWING",
  "original_artifacts":[14158848286,14161823401],
  "partial_adaptation":"Original immediate 2-slash bounded local-only ATTACK feedback on existing HUD action button; old 0.85s client throttle",
  "authoritative_attack":"unchanged original Tool and server owner",
  "other_68_selected_source_bytes_unchanged":True,
  "full_original_behavior_parity":"NOT_TESTED",
  "studio_android_fun":"NOT_TESTED",
  "rollback":"off69_fb019 + OFF69_PRE_FB019_EXACT.rbxlx"}
 (root/receiptname).write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
 print("GQ8_FB019_REAL69_69_ROUTES_ONE_HUD_PORT_PASS")
if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--base",type=pathlib.Path)
 parser.add_argument("--head",default="CANDIDATE")
 parser.add_argument("--self-test",action="store_true")
 args=parser.parse_args()
 if args.self_test:selftest()
 else:
  need(args.base is not None,"BASE_MISSING")
  run(args.base,args.head)
