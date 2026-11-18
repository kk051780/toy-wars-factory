#!/usr/bin/env python3
"""GQ828 REAL62->REAL63: patch the actual *single* SevenRoleCombat and HUD.
Original real62 is an immutable same-official-head Place artifact. The original
58 other real62 sources must stay byte-identical, with ONE new policy module.
No second Combat/HP/Score/Remote/Store authority and no main/publish/Robux.
"""
from __future__ import annotations
import argparse, json, re, hashlib, sys
from pathlib import Path
from xml.etree import ElementTree as ET
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"EGGRUMBLE-HUD-INTEL-20261119"))
from compose_real40 import contents, project_for, digest
OFFICIAL_SHA="b15db4b9ad1f1f4c1f02fb0976eb3c2f6db8a6ff"
COMBAT=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
HUD=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_HudIntelRuntime")
VIEW=("ReplicatedStorage","EGGRUMBLE_HudPresentationPolicy")
POLICY=("ServerScriptService","EGGRUMBLE_BasicMobilityPolicy")

def only(s,old,new,label):
 n=s.count(old)
 if n!=1:raise ValueError("RED_"+label+"_ANCHOR_"+str(n))
 return s.replace(old,new,1)

CORE_ACTION=r'''
-- Authoritative quick attack + grounded evasion share the original
-- SevenRoleCombat session, damage/LOS/neutral-KO and safeMove owners.
-- No new RemoteEvent and no second TakeDamage site.
local function executeCoreAction(session:any,p:Player,role:string,
 action:string,tool:Tool)
 if tool.Parent~=p.Character or not p.Parent or session.rules.phase~="ACTIVE"
  or p:GetAttribute("EGGRUMBLE_Role")~=role
  or p:GetAttribute("EGGRUMBLE_QueuedMode")~=session.mode
  or p:GetAttribute("EGGRUMBLE_Eliminated")==true then return end
 local state=session.rules.castles[tostring(p.UserId)]
 if not state or not state.alive then return end
 local char,root,h=characterOf(p)
 if not char or not root or not h then return end
 local downed=p:GetAttribute("EGGRUMBLE_Downed")==true
  or h:GetAttribute("EGGRUMBLE_Downed")==true
 local carrying=(type(state.heldEggs)=="number" and state.heldEggs>0)
  or p:GetAttribute("EGGRUMBLE_CarryingEgg")==true
 local realm=if p:GetAttribute("EGGRUMBLE_RealmDepth")=="SUBSEA"
  or h.SeatPart and h.SeatPart.Parent and h.SeatPart.Parent.Name:find("_SEA_")
  then "SEA" elseif h.SeatPart then "SKY" else "LAND"
 local ledger=lastByPlayer[p.UserId]
 if not ledger then ledger={};lastByPlayer[p.UserId]=ledger end
 local now=os.clock()
 local c={
  serverVerified=true,roleVerified=true,ownsTool=true,now=now,
  -- Original arena Name repeats, so cooldown keys must use the unique round table.
  matchEpoch=tostring(session),mode=session.mode,phase=session.rules.phase,
  alive=true,castleAlive=true,downed=downed,eliminated=false,
  carryingEgg=carrying,seated=h.SeatPart~=nil,
  realm=realm,onGround=h.FloorMaterial~=Enum.Material.Air,
 }
 local ok,key,spec=CoreAction.authorize(ledger,role,action,now,c)
 if not ok or not key then return end
 if action=="DODGE" then
  -- Original author safeMove checks forward collision and solid ground.
  -- Blocked displacement consumes no cooldown and changes no objective state.
  if not safeMove(char,root,spec.distance) then return end
  CoreAction.take(ledger,role,action,now,c)
  p:SetAttribute("EGGRUMBLE_DodgeCastSerial",
   (p:GetAttribute("EGGRUMBLE_DodgeCastSerial") or 0)+1)
  return
 end
 -- Direct normal attacks do not apply skill status effects or damage multipliers
 -- in a new owner: existing Swarm/Combat handle all existing guards and KO.
 local consumed=CoreAction.take(ledger,role,action,now,c)
 if not consumed then return end
 local center=rootAdvance(root,spec.reach)
 local hits=neutralAndBotHit(session,p,root,char,center,
  spec.radius,spec.damage,JOBS[role].color,spec.shape)
 ImpactFeedback.attacker(p,role,"A",hits)
 p:SetAttribute("EGGRUMBLE_BasicCastSerial",
  (p:GetAttribute("EGGRUMBLE_BasicCastSerial") or 0)+1)
end
'''
EQUIP_ADD=r'''
 -- Independent ordinary attack and grounded evasion, both server Tool owners
 -- stay inside this ONE existing role Combat module and its match session.
 for _,action in ipairs({"BASIC","DODGE"}) do
  local core=Instance.new("Tool")
  core.Name=if action=="BASIC" then "EGGRUMBLE_BASIC_ATTACK"
    else "EGGRUMBLE_DODGE_STEP"
  core.ToolTip=if action=="BASIC" then "通常攻撃｜役職別近距離連撃"
    else "回避｜前方に短く移動、障害物・卵運搬は不可"
  core.RequiresHandle=false
  core.CanBeDropped=false
  core.Activated:Connect(function()
   if core.Parent~=p.Character then return end
   executeCoreAction(session,p,role,action,core)
  end)
  core.Parent=backpack
 end
'''
def patch_combat(source):
 source=only(source,
  'local CombatBalance=require(script.Parent:WaitForChild("EGGRUMBLE_CombatBalance"))',
  'local CombatBalance=require(script.Parent:WaitForChild("EGGRUMBLE_CombatBalance"))\n'
  'local CoreAction=require(script.Parent:WaitForChild("EGGRUMBLE_BasicMobilityPolicy"))',
  "ONE_POLICY_IMPORT")
 source=only(source,'local function execute(session:any,p:Player,role:string,slot:string)',
   CORE_ACTION+'\nlocal function execute(session:any,p:Player,role:string,slot:string)',
   "ONE_ORIGINAL_EXECUTE_ENTRY")
 # Must attach only to the original HeroCombat.equip just before clear().
 source=only(source,'\nend\nfunction HeroCombat.clear(p:Player)',
   '\n'+EQUIP_ADD+'\nend\nfunction HeroCombat.clear(p:Player)',
   "ONE_EQUIP_END")
 # Preserve original cleanup of skill/MUSOU and additionally remove both new
 # tools. Anchor the real selected Real55 source exact lines rather than guessing.
 for name in ("instance","item"):
  pattern=re.compile(r'if '+name+r':IsA\("Tool"\) and \([^\n]*?'
                     +name+r'\.Name=="EGGRUMBLE_MUSOU_AWAKEN"\) then '
                     +name+r':Destroy\(\) end')
  matches=pattern.findall(source)
  if len(matches)!=1:raise ValueError("RED_REAL59_"+name.upper()+"_CLEANUP_"+str(len(matches)))
  old=matches[0]
  new=old.replace(') then '+name+':Destroy() end',
      ' or '+name+'.Name=="EGGRUMBLE_BASIC_ATTACK"'
      ' or '+name+'.Name=="EGGRUMBLE_DODGE_STEP") then '+name+':Destroy() end')
  source=only(source,old,new,"REAL59_"+name.upper()+"_EQUIP_CLEANUP")
 if source.count('EGGRUMBLE_BASIC_ATTACK')!=3 or source.count('EGGRUMBLE_DODGE_STEP')!=3:
  raise ValueError("RED_MISSING_TOOL_CREATE_AND_TWO_CLEAR_ROUTES")
 if source.count("executeCoreAction(session,p,role,action,core)")!=1:
  raise ValueError("RED_CLIENT_ACTION_EXECUTION_DUPLICATION")
 return source

def patch_view(source):
 # REAL59 small portrait: top action menus must not obscure HP/status.
 source=only(source,'local menuY = math.min(133, h * .18)',
  'local menuY = math.max(62, math.min(133, h * .18))',"PORTRAIT_MENU_STATUS")
 # Square buttons overlap at a corner despite center-distance circle tests.
 source=only(source,'MUSOU = at(x - 66, h - 35, 46, "無双")',
  'MUSOU = at(x - 55, h - 35, 46, "無双")',"PORTRAIT_INVUL_MUSOU")
 return source

def patch_hud(source):
 source=only(source,'actions.DODGE.Visible=false -- requires an existing authorized dodge owner',
  'actions.DODGE.Visible=false -- enabled only when original owned dodge Tool exists',
  "DODGE_UNSUPPORTED_TEXT")
 source=only(source,'local reserved=p.DODGE','local reserved=p.CONTEXT',"SEPARATE_SKILL_AND_DODGE_ANCHOR")
 source=only(source,'local function musouTool()',
   'local function dodgeTool()\n return ownedToolByName("EGGRUMBLE_DODGE_STEP")\nend\n'
   'local function basicTool()\n return ownedToolByName("EGGRUMBLE_BASIC_ATTACK")\nend\n'
   'local function musouTool()', "ACTUAL_SERVER_TOOL_LOOKUP")
 source=only(source,' local basic=toolWith("EGGRUMBLE_BASIC_")\n'
  ' -- The current 55-source server has no dedicated basic attack Tool.\n'
  ' -- Use only its real A skill (clearly labeled) until Combat owner adds basic.\n'
  ' activate(basic[1] or slotTool("A"))',
   ' activate(basicTool() or slotTool("A"))',"REAL_BASIC_ATTACK_BUTTON")
 source=only(source,'actions.INVUL.Activated:Connect(function()',
   'actions.DODGE.Activated:Connect(function()\n'
   ' if not mapSnapshot then return end\n'
   ' local tool=dodgeTool()\n'
   ' if tool then closeDrawer();activate(tool) end\n'
   'end)\n'
   'actions.INVUL.Activated:Connect(function()', "SERVER_DODGE_TOOL_ACTION")
 source=only(source,
  'actions.ATTACK.Visible=#toolWith("EGGRUMBLE_BASIC_")>0 or slotTool("A")~=nil',
  'actions.ATTACK.Visible=basicTool()~=nil or slotTool("A")~=nil', "ATTACK_VISIBLE")
 source=only(source,
  'actions.ATTACK.Text=toolWith("EGGRUMBLE_BASIC_")[1] and "攻撃" or "技A"',
  'actions.ATTACK.Text=basicTool() and "攻撃" or "技A"', "TRUE_BASIC_LABEL")
 source=only(source,
  'actions.ITEM.Text=#toolWith("EGGRUMBLE_ITEM_")>0 and "道具 ▼" or "道具 0"',
  'actions.ITEM.Text=#toolWith("EGGRUMBLE_ITEM_")>0 and "道具 ▼" or "道具 0"\n'
  ' actions.DODGE.Visible=dodgeTool()~=nil', "DODGE_VISIBLE")
 source=only(source,
  ' actions.ATTACK.Visible=actions.ATTACK.Visible and inMatch\n'
  ' skillUse.Visible=skillUse.Visible and inMatch',
  ' actions.ATTACK.Visible=actions.ATTACK.Visible and inMatch\n'
  ' actions.DODGE.Visible=actions.DODGE.Visible and inMatch\n'
  ' skillUse.Visible=skillUse.Visible and inMatch', "BATTLE_ONLY_DODGE")
 if 'local reserved=p.DODGE' in source:
  raise ValueError("RED_SELECTED_SKILL_COVERS_DODGE")
 source=only(source,
  ' choices[i].Size=UDim2.new(1,-12,0,37)',
  ' choices[i].Size=UDim2.new(1,-12,0,31)',"FOUR_CHOICE_HEIGHT")
 source=only(source,
  ' choices[i].Position=UDim2.fromOffset(6,5+(i-1)*40)',
  ' choices[i].Position=UDim2.fromOffset(6,5+(i-1)*33)',"FOUR_CHOICE_SPACING")
 source=only(source,
  ' drawer.Size=UDim2.fromOffset(math.min(178,w*.23),170)\n'
  ' drawer.Position=UDim2.fromOffset(math.max(w-195,w*.72),math.min(h*.35,147))',
  ' local dw=math.min(178,math.max(104,math.floor(w*.25)))\n'
  ' local menuBottom=math.max(p.ITEM.y+p.ITEM.size/2,p.SKILL.y+p.SKILL.size/2)\n'
  ' local dy=math.max(48,math.min(math.floor(menuBottom+8),h-150))\n'
  ' drawer.Size=UDim2.fromOffset(dw,145)\n'
  ' drawer.Position=UDim2.fromOffset(math.max(8,w-dw-8),dy)',
  "DRAWER_OVERLAP")
 source=only(source,
  ' actions.ATTACK.Visible=actions.ATTACK.Visible and inMatch\n'
  ' actions.DODGE.Visible=actions.DODGE.Visible and inMatch\n'
  ' skillUse.Visible=skillUse.Visible and inMatch',
  ' -- Menu opens as a compact modal, so its controls never visually stack\n'
  ' -- over combat buttons. This is visual-only, no client gameplay grant.\n'
  ' local selecting=drawer.Visible\n'
  ' actions.ATTACK.Visible=actions.ATTACK.Visible and inMatch and not selecting\n'
  ' actions.DODGE.Visible=actions.DODGE.Visible and inMatch and not selecting\n'
  ' skillUse.Visible=skillUse.Visible and inMatch and not selecting',
  "MODAL_ATTACK_DODGE")
 source=only(source,
  ' actions.INVUL.Visible=inMatch\n'
  ' actions.MUSOU.Visible=inMatch',
  ' actions.INVUL.Visible=inMatch and not drawer.Visible\n'
  ' actions.MUSOU.Visible=inMatch and not drawer.Visible',
  "MODAL_MODE_BUTTONS")
 source=only(source,
  '  mapBox.Size=UDim2.fromOffset(math.floor(math.min(w*.43,340)),math.floor(math.min(h*.66,285)))\n'
  '  mapBox.Position=UDim2.fromOffset(9,math.max(8,math.floor(h*.12)))',
  '  local mw=math.floor(math.min(w*.43,340))\n'
  '  local my=math.max(8,math.floor(h*.12))\n'
  '  local moveTop=p.MOVE.y-p.MOVE.size/2\n'
  '  local mh=math.max(60,math.min(math.floor(math.min(h*.66,285)),math.floor(moveTop-my-10)))\n'
  '  mapBox.Size=UDim2.fromOffset(mw,mh)\n'
  '  mapBox.Position=UDim2.fromOffset(hand=="LEFT" and (w-mw-9) or 9,my)',
  "MAP_MOVE_CLEARANCE")
 if source.count('actions.DODGE.Activated:Connect(')!=1:
  raise ValueError("RED_DUPLICATE_DODGE_CLICK")
 return source

def run(place,receipt,out):
 data=json.loads(receipt.read_text(encoding="utf8"))
 assert data.get("official_rc_adopted") is True,"RED_REAL62_NOT_OFFICIAL"
 assert data.get("tested_head")==OFFICIAL_SHA,"RED_REAL62_WRONG_OFFICIAL_HEAD"
 assert data.get("combined_count")==62 and data.get("host_class")=="Script","RED_REAL62_PROFILE_OR_HOST_MISSING"
 assert data.get("real62_sha256")==digest(place),"RED_REAL62_PHYSICAL_SHA_DRIFT"
 src,classes=contents(ET.parse(place).getroot())
 if len(src)!=62 or COMBAT not in src or HUD not in src or VIEW not in src or POLICY in src:
  raise ValueError("RED_NOT_UNIQUE_62_SOURCES")
 host=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
 if src.get(host,(None,None))[0]!="Script":
  raise ValueError("RED_NEWEST_OFFICIAL_HOST_NOT_AUTOSTART")
 if "local function startSession(" not in src[host][1]:
  raise ValueError("RED_NEWEST_HOST_ACTIVATION_CONTENT")
 for route in (("ServerScriptService","GQ8_TradeJournalContract"),
               ("ServerScriptService","GQ8_TradeEscrowReducer"),
               ("StarterPlayer","StarterPlayerScripts","GQ8_TradeReview")):
  if route not in src:raise ValueError("RED_REAL62_TRADE_ROUTE_DROPPED_"+"/".join(route))
 if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
 out.mkdir(parents=True)
 orig=dict(src)
 off=out/"off62";off.mkdir()
 _,offIndex=project_for(src,classes,off,"GQ828_OFF62_EXACT")
 src[COMBAT]=(orig[COMBAT][0],patch_combat(orig[COMBAT][1]))
 src[HUD]=(orig[HUD][0],patch_hud(orig[HUD][1]))
 src[VIEW]=(orig[VIEW][0],patch_view(orig[VIEW][1]))
 src[POLICY]=("ModuleScript",(HERE/"EGGRUMBLE_BasicMobilityPolicy.luau").read_text(encoding="utf8"))
 assert len(src)==63
 for route in set(orig)-{COMBAT,HUD,VIEW}:
  if src[route]!=orig[route]:raise ValueError("RED_DUPLICATE_CORE_OVERWRITE")
 assert sum("EGGRUMBLE_SwarmCombat"==k[-1] for k in src)==1
 assert sum("EGGRUMBLE_SevenRoleCombat"==k[-1] for k in src)==1
 classes[POLICY]="ModuleScript"
 on=out/"on63";on.mkdir()
 _,onIndex=project_for(src,classes,on,"GQ828_REAL63_BASIC_DODGE")
 report={
  "feature_id":"GQ828_BASIC_DODGE_REAL63_20261119",
  "official_parent_sha":OFFICIAL_SHA,
  "parent_original_sources":62,"candidate_sources":63,
  "original_unchanged":59,
  "original_modified":["/".join(COMBAT),"/".join(HUD),"/".join(VIEW)],
  "added_module":"/".join(POLICY),
  "original_parent_place_sha256":digest(place),
  "host_original_class":"Script",
  "trade_original_three_sources_retained":True,
  "parent_host_fix_retained":True,
  "on_sources":onIndex,"off_sources":offIndex,
  "native":"PENDING","rojo":"PENDING","off62":"PENDING",
  "official_rc_adopted":False,"studio2client":"NOT_TESTED",
  "android15min":"NOT_TESTED","art_fun":"NO_GO",
  "robuxtx_enabled":False,"roblox_published":False,
  "combat_owner_count":1,"remote_added":0,"direct_damage_site_added":0,
  "rollback":"OFF62 original physical canonical Host+HUD+Trade source selected"
 }
 (out/"REAL63_RECEIPT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print("GQ828_REAL63_ORIGINAL59_PRESERVED_3_SELECTED_PATCHED_1_POLICY_PASS")

if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--place",type=Path,required=True)
 ap.add_argument("--receipt",type=Path,required=True)
 ap.add_argument("--out",type=Path,required=True)
 a=ap.parse_args()
 run(a.place,a.receipt,a.out)
