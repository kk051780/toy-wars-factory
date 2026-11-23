#!/usr/bin/env python3
"""Source-select RC85/RC86 realm-discovery feedback into the existing REAL69 HUD, no duplicate authority."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, sys
HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "gq8_rc85_rc86_real68_nonloss_20261120"))
ROUTE="StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime"
MARKER="GQ8_RC85_RC86_LEGACY_EXPLORE_DISCOVERY_TOAST_REAL69_20261120"
OLD_SHA="94d78731d69447a2c5d5a1b4f2058e3eda15aff345327837f0e46f039b62f7c1"
APPEND=r'''

-- GQ8_RC85_RC86_LEGACY_EXPLORE_DISCOVERY_TOAST_REAL69_20261120
-- Preserve original 4-realm and 6-shard discovery from the server; no duplicate Remote/Game/Store.
-- The former RC85 persistent RealmHuntHUD is adapted into a nonblocking 3.8-second in-match toast.
local exploreToast=Instance.new("TextLabel")
exploreToast.Name="LegacyExploreDiscoveryToast"
exploreToast.AnchorPoint=Vector2.new(.5,0)
exploreToast.Position=UDim2.new(.5,0,0,55)
exploreToast.Size=UDim2.fromOffset(218,39)
exploreToast.BackgroundColor3=Color3.fromRGB(27,47,65)
exploreToast.BackgroundTransparency=.15
exploreToast.BorderSizePixel=0
exploreToast.Font=Enum.Font.GothamBold
exploreToast.TextColor3=Color3.fromRGB(255,242,189)
exploreToast.TextSize=14
exploreToast.TextWrapped=true
exploreToast.ZIndex=24
exploreToast.Visible=false
exploreToast.Parent=gui
rounded(exploreToast,8)
local legacyPrefix="EGGRUMBLE_LegacyExplore_"
local lastExploreMode=player:GetAttribute(legacyPrefix.."Mode")
local lastRealmCount=player:GetAttribute(legacyPrefix.."Realms") or 0
local lastShardCount=player:GetAttribute(legacyPrefix.."Shards") or 0
local toastEpoch=0
local function hideLegacyToast()
 toastEpoch+=1
 exploreToast.Visible=false
end
player:GetAttributeChangedSignal(legacyPrefix.."Mode"):Connect(function()
 local mode=player:GetAttribute(legacyPrefix.."Mode")
 if mode~=lastExploreMode then
  lastExploreMode=mode
  lastRealmCount=0
  lastShardCount=0
  hideLegacyToast()
 end
end)
local function showLegacyDiscovery()
 local mode=player:GetAttribute(legacyPrefix.."Mode")
 if mode~="TEAM" and mode~="BR" then hideLegacyToast();return end
 local realms=player:GetAttribute(legacyPrefix.."Realms")
 local shards=player:GetAttribute(legacyPrefix.."Shards")
 if type(realms)~="number" or type(shards)~="number" then return end
 if realms~=realms or shards~=shards then return end
 realms=math.clamp(math.floor(realms),0,4)
 shards=math.clamp(math.floor(shards),0,6)
 if realms<=lastRealmCount and shards<=lastShardCount then
  lastRealmCount=realms;lastShardCount=shards;return
 end
 lastRealmCount=realms;lastShardCount=shards
 if not gui.Enabled then return end
 toastEpoch+=1
 local myEpoch=toastEpoch
 local completed=player:GetAttribute(legacyPrefix.."Complete")==true
 exploreToast.Text=completed and "秘境探索クリア！ 4/4・星片 6/6"
  or string.format("秘境 %d/4  ✦  星片 %d/6",realms,shards)
 exploreToast.Visible=true
 task.delay(3.8,function()
  if toastEpoch==myEpoch and exploreToast.Parent==gui then exploreToast.Visible=false end
 end)
end
player:GetAttributeChangedSignal(legacyPrefix.."Realms"):Connect(showLegacyDiscovery)
player:GetAttributeChangedSignal(legacyPrefix.."Shards"):Connect(showLegacyDiscovery)
-- Do not show counters on initial join as if freshly discovered.
'''
def demand(ok,msg):
 if not ok: raise ValueError("RED_RC85_EXPLORE_TOAST_"+msg)
def sha(s): return hashlib.sha256(s).hexdigest()
def run(base,head):
 from verify_nonloss import project_scan
 project=base/"EGGRUMBLE_REAL69.project.json"
 receipt_path=base/"REAL69_LEGACY_INTAKE_RECEIPT.json"
 demand(project.is_file() and receipt_path.is_file(),"PARENT_ABSENT")
 before=project_scan(base,project.name)
 demand(len(before)==69 and ROUTE in before,"BASE_ROUTES")
 demand(before[ROUTE]["sha256"]==OLD_SHA,"ORIGINAL_HUD_SHA")
 demand(before[ROUTE]["class"]=="LocalScript","HUD_CLASS")
 receipt=json.loads(receipt_path.read_text())
 demand(receipt.get("selected_source_count")==69 and len(receipt.get("source_hashes",{}))==69,"RECEIPT_COUNT")
 demand(all(receipt["source_hashes"].get(k)==v["sha256"] for k,v in before.items()),"BASE_SOURCE_DRIFT")
 demand("rc85_realm_hunt_discovery_toast" not in receipt,"ALREADY_ACCEPTED")
 target=base/before[ROUTE]["path"]
 old=target.read_bytes()
 demand(MARKER.encode() not in old and old.rstrip().endswith(b"end)"),"HUD_STRUCTURE")
 demand(not (base/"off69_discovery").exists(),"ROLLBACK_EXISTS")
 demand((base/"EGGRUMBLE_REAL69_PRIVATE.rbxlx").is_file(),"OLD_PLACE_ABSENT")
 off=base/"off69_discovery";off.mkdir()
 shutil.copytree(base/"sources",off/"sources")
 shutil.copy2(project,off/project.name)
 shutil.copy2(receipt_path,off/receipt_path.name)
 shutil.copy2(base/"EGGRUMBLE_REAL69_PRIVATE.rbxlx",base/"OFF69_PRE_DISCOVERY_EXACT.rbxlx")
 target.write_bytes(old.rstrip()+APPEND.encode("utf-8"))
 after=project_scan(base,project.name)
 demand(len(after)==69 and set(before)==set(after),"ROUTE_NONLOSS")
 demand(sum(after[k]["sha256"]!=before[k]["sha256"] for k in before)==1,"ONE_SOURCE_ONLY")
 demand(all(after[k]["class"]==before[k]["class"] for k in before),"CLASSES_NONLOSS")
 receipt["source_hashes"][ROUTE]=after[ROUTE]["sha256"]
 receipt["rc85_realm_hunt_discovery_toast"]={
   "feature_id":MARKER,"legacy_flags":["REALM_HUNT_V1","STAR_SHARDS_V1"],
   "original_rc85_artifact":14158848286,"original_rc86_artifact":14161823401,
   "adaptation":"existing server 4-realm 6-shard counters -> transient 3.8-second toast",
   "old_persistent_hud_restored":False,"all_prior_real69_routes_preserved":True,
   "old_48_flag_semantic_parity":"NOT_PROVEN","studio_android_fun":"NOT_TESTED",
   "rollback":"off69_discovery + OFF69_PRE_DISCOVERY_EXACT.rbxlx"}
 receipt["build_head"]=head
 receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
 print("GQ8_REAL69_LEGACY_DISCOVERY_ONE_HUD_NONLOSS_PASS")
def selftest():
 demand(APPEND.count(MARKER)==1,"MARKER")
 for text in ('3.8','exploreToast.Visible=false','legacyPrefix.."Mode"','legacyPrefix.."Realms"','legacyPrefix.."Shards"','legacyPrefix.."Complete"','if not gui.Enabled then return end'):
  demand(text in APPEND,"MISSING_"+text)
 for forbidden in ('Instance.new("RemoteEvent")','DataStoreService','SetAttribute(','FireServer('):
  demand(forbidden not in APPEND,"FORBIDDEN_"+forbidden)
 print("GQ8_REAL69_LEGACY_DISCOVERY_SELFTEST_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--base",type=pathlib.Path);p.add_argument("--head",default="PRIVATE");p.add_argument("--self-test",action="store_true");a=p.parse_args()
 if a.self_test:selftest()
 else:
  demand(a.base is not None,"MISSING_BASE")
  run(a.base,a.head)
