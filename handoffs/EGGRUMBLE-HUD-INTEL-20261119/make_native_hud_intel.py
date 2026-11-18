#!/usr/bin/env python3
"""Generate native Luau regression programs from the actual two committed sources."""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parent
HUD = (ROOT / "HudPresentationPolicy.luau").read_text(encoding="utf8")
MAP = (ROOT / "MapVisibilityPolicy.luau").read_text(encoding="utf8")
CLIENT = (ROOT / "EGGRUMBLE_HudIntelRuntime.client.luau").read_text(encoding="utf8")

def check_touch_runtime_source() -> None:
    """The real Roblox client must re-enable buttons after lobby/map reset.

    Source-exact structural gate complements native pure-policy tests. It does
    not claim Studio input or device UX verification.
    """
    required = {
        "battle only chrome": "gui.Enabled=inMatch",
        "visible Musou": "actions.MUSOU.Visible=inMatch",
        "visible Invul": "actions.INVUL.Visible=inMatch",
        "actual MUSOU Tool": 'return ownedToolByName("EGGRUMBLE_MUSOU_AWAKEN")',
        "actual INVUL Tool": 'return ownedToolByName("迎撃覚醒")',
        "exact original Musou READY IN": 'local readyIn=player:GetAttribute("EGGRUMBLE_MusouReadyIn")',
        "server original Musou phase": 'local phaseM=player:GetAttribute("EGGRUMBLE_MusouPhase")',
        "gated Musou ready": 'local verifiedM=musou~=nil and phaseM=="OFF" and type(readyIn)=="number"',
        "invul armed": 'local armed=phaseI=="ARMED"',
        "invul awakened": 'local awakened=phaseI=="AWAKENED"',
        "server owned trigger only": "closeDrawer();activate(tool)",
        "first existing skill takes attack slot until normal combat owner implements basic": 'actions.ATTACK.Visible=#toolWith("EGGRUMBLE_BASIC_")>0 or slotTool("A")~=nil',
        "independent selected skill trigger": "activate(slotTool(selectedSlot))",
        "skill use uses reserved dodge area": "local reserved=p.DODGE",
        "actual dodge hidden until owner implements": 'actions.DODGE.Visible=false -- requires an existing authorized dodge owner',
        "item source honest count": 'actions.ITEM.Text=#toolWith("EGGRUMBLE_ITEM_")>0 and "道具 ▼" or "道具 0"',
        "handedness refresh": "w==lastW and h==lastH and hand==lastHand",
        "handedness cache": "lastW,lastH,lastHand=w,h,hand",
    }
    for case, anchor in required.items():
        assert CLIENT.count(anchor) == 1 or (case == "server owned trigger only" and CLIENT.count(anchor)==2), "RED_HUD_RUNTIME_" + case.replace(" ", "_")
    for forbidden in (
        'player:GetAttribute("EGGRUMBLE_InvulReady")',
        'player:GetAttribute("EGGRUMBLE_MusouReady")',
        'return ownedToolByName("EGGRUMBLE_INVUL_',
        '"remote:FireServer("',
    ):
        assert forbidden not in CLIENT, "RED_NONAUTHORITATIVE_POWER_BUTTON_" + forbidden
    assert "gui.Enabled=inMatch" in CLIENT, "RED_BATTLE_UI_OBSCURES_LOBBY"
    assert "remote:FireServer(" not in CLIENT, "RED_CLIENT_FORGED_AUTHORITY"
    # Note: exact upstream Real55 original Tool names/attributes are checked
    # again by the Real59 workflow against the 55 physical selected sources.

TEST = r'''
local H = Hud
local M = Map
local function close(a,b)
  return math.abs(a-b) < 0.001
end
local function separated(a,b)
  local dx,dy=a.x-b.x,a.y-b.y
  return math.sqrt(dx*dx+dy*dy) >= (a.size+b.size)*.5 - 1
end
for _,shape in ipairs({{851,393},{1280,720},{393,851},{320,260}}) do
  for _,hand in ipairs({"RIGHT","LEFT"}) do
    local l=H.layout(shape[1],shape[2],hand)
    local p=l.anchors
    for _,name in ipairs({"ATTACK","JUMP","DODGE","INVUL","MUSOU","ITEM","SKILL","MAP","MOVE"}) do
      assert(type(p[name])=="table","RED_MISSING_TOUCH_"..name)
      assert(p[name].x-p[name].size/2>=0 and p[name].x+p[name].size/2<=shape[1],"RED_TOUCH_OFFSCREEN_"..name)
      assert(p[name].y-p[name].size/2>=0 and p[name].y+p[name].size/2<=shape[2],"RED_TOUCH_OFFSCREEN_"..name)
    end
    local actions={"ATTACK","JUMP","DODGE","INVUL","MUSOU","ITEM","SKILL"}
    for i=1,#actions do
      for j=i+1,#actions do
        assert(separated(p[actions[i]],p[actions[j]]),"RED_OVERLAP_"..actions[i].."_"..actions[j])
      end
    end
    local clear=l.combatClear
    assert(clear.x1>clear.x0 and clear.y1>clear.y0,"RED_COMBAT_VIEW_AREA")
    assert(p.ATTACK.x < clear.x0 or p.ATTACK.x > clear.x1,"RED_ATTACK_COVERS_BATTLE")
    assert(p.MAP.x < clear.x0 or p.MAP.x > clear.x1,"RED_MAP_COVERS_BATTLE")
    local chrome=l.chrome
    assert(type(chrome)=="table","RED_HUD_CHROME_ABSENT")
    local status,bar,map=chrome.status,chrome.musouBar,chrome.map
    assert(status.x>=0 and status.x+status.w<=shape[1]
      and status.y>=0 and status.y+status.h<=clear.y0,
      "RED_HP_STATUS_OUT_OF_SAFE_TOP")
    assert(bar.x>=status.x and bar.x+bar.w<=status.x+status.w
      and bar.y>status.y+status.h and bar.y+bar.h<=clear.y0,
      "RED_MUSOU_BAR_OBSCURES_BATTLE")
    assert(map.x>=0 and map.x+map.w<=shape[1],"RED_MAP_OUT_OF_SAFE_HORIZONTAL")
    assert(status.x>=map.x+map.w+8
      or status.x+status.w<=map.x-8,
      "RED_HP_OVERLAPS_MAP_ON_COMPACT_OR_LEFTHAND")
  end
end
local sync=H.display({})
assert(sync.state=="SYNCING" and sync.buttons.MUSOU==false and sync.hpText=="--/--","RED_FAKE_CLIENT_READY")
local snap={
  serverAuthoritative=true,hp=150,maxHp=200,
  musouCharge=.8,musouReady=true,invulReady=true,
  hasEquippedItem=true,hasEquippedSkill=true,
  statuses={{label="burn",priority=1},{label="freeze",priority=4},{label="poison",priority=3},{label="wind",priority=2}},
}
local ui=H.display(snap)
assert(ui.hpText=="150/200" and ui.musouCharge==.8,"RED_STATUS_VIEW")
assert(#ui.statuses==3 and ui.hiddenStatusCount==1 and ui.statuses[1].label=="freeze","RED_STATUS_PRIORITY")
assert(ui.buttons.MUSOU and ui.buttons.INVUL,"RED_FREE_CORE_BUTTON")
snap.invulArmed=true
ui=H.display(snap)
assert(ui.phase=="ARMED" and not ui.buttons.MUSOU and not ui.buttons.INVUL,"RED_ARMed_EXCLUSION")
snap.invulArmed=false
snap.invulRemaining=7
ui=H.display(snap)
assert(ui.phase=="INVUL" and not ui.buttons.MUSOU,"RED_INVUL_OVERLAP")
snap.invulRemaining=0;snap.carryingEgg=true
ui=H.display(snap)
assert(not ui.buttons.MUSOU and not ui.buttons.INVUL,"RED_EGG_BYPASS")
local menu=H.menuItems("ITEM",{{id="s1",kind="ITEM",serverOwned=true,usable=true},{id="h4",kind="ITEM",serverOwned=false,usable=true},{id="a",kind="SKILL",serverOwned=true,usable=true}})
assert(#menu==1 and menu[1].id=="s1","RED_UNOWNED_PURCHASE_BYPASS")
assert(#H.menuItems("PURCHASE",menu)==0,"RED_UNSAFE_PURCHASE")
local fog=M.newExploration(0,0)
local function viewer(role)
 return {playerId="p1",team="RED",role=role,layer="LAND",
   x=0,z=0,explored=fog,serverVerified=true}
end
local hiddenEnemy={id="secret",kind="ENEMY",x=160,z=0,team="BLUE",layer="LAND",serverLineOfSight=false}
local castle={id="castle",kind="CASTLE",x=700,z=900,team="BLUE",layer="LAND"}
local view=M.project(viewer("WARRIOR"),{hiddenEnemy,castle},100)
assert(#view==1 and view[1].id=="castle","RED_HIDDEN_POSITION_EXFILTRATION")
local function one(role,kind,pulse,marker)
 local v=viewer(role)
 v.pulse={kind=pulse,expiresAt=108,serverVerified=true}
 local r=M.project(v,{marker},100)
 assert(#r==1 and r[1].precision=="SECTOR","RED_ROLE_NO_REVEAL_"..role)
 assert(close(r[1].x,200) and close(r[1].z,40),"RED_PRECISE_LOCATION_LEAK_"..role)
 assert(#M.project(v,{marker},108)==0,"RED_EXPIRED_REVEAL_"..role)
 v.pulse.serverVerified=false
 assert(#M.project(v,{marker},100)==0,"RED_FORGED_PULSE_"..role)
end
one("WARRIOR","CASTLE_GATE","SIEGE_SENSE",{id="g",kind="CASTLE_GATE",x=160,z=0})
one("MAGE","ELEMENT","MAGIC_SENSE",{id="a",kind="ELEMENT",x=160,z=0})
one("NINJA","ENEMY_TRAIL","TRAIL_SENSE",{id="t",kind="ENEMY_TRAIL",x=160,z=0,layer="LAND"})
one("TRAPPER","ENEMY","ENEMY_SENSE",hiddenEnemy)
one("BUILDER","RESOURCE","RESOURCE_SENSE",{id="r",kind="RESOURCE",x=160,z=0})
one("BEAST","NEUTRAL","BEAST_SENSE",{id="n",kind="NEUTRAL",x=160,z=0,layer="LAND"})
one("ZOMBIE","NEUTRAL","CURSE_SENSE",{id="z",kind="NEUTRAL",x=160,z=0,layer="LAND"})
local v=viewer("TRAPPER")
v.pulse={kind="ENEMY_SENSE",expiresAt=200,serverVerified=true}
local sea={id="sub",kind="ENEMY",x=160,z=0,team="BLUE",layer="SEA",serverLineOfSight=true}
assert(#M.project(v,{sea},100)==0,"RED_CROSS_LAYER_WALLHACK")
local near={id="near",kind="ENEMY",x=40,z=0,team="BLUE",layer="LAND",serverLineOfSight=true}
assert(#M.project(v,{near},100)==1 and M.project(v,{near},100)[1].precision=="EXACT","RED_LEGIT_LOS_BROKEN")
near.stealthed=true
assert(#M.project(v,{near},100)==1 and M.project(v,{near},100)[1].precision=="SECTOR","RED_STEALTH_EXACT_LEAK")
near.serverLineOfSight=false
v.pulse=nil
assert(#M.project(v,{near},100)==0,"RED_NO_LOS_HIDE_BROKEN")
print("GQ8_HUD_INTEL_NATIVE_LAYOUT_STATUS_FOG_7ROLE_PRIVACY_PASS")
'''
def wrap(hud: str, map_: str) -> str:
    return "local Hud=(function()\n" + hud + "\nend)()\nlocal Map=(function()\n" + map_ + "\nend)()\n" + TEST

def main() -> None:
    a=argparse.ArgumentParser()
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    check_touch_runtime_source()
    assert "RemoteEvent" not in HUD+MAP
    for bad in ("DataStoreService","MarketplaceService","FireServer(","OnServerEvent","TakeDamage(","Humanoid.Health"):
        assert bad not in HUD+MAP,bad
    (args.out/"good.luau").write_text(wrap(HUD, MAP),encoding="utf8")
    changes={
        "auth":(HUD.replace("snapshot.serverAuthoritative ~= true","snapshot.serverAuthoritative == true"),MAP),
        "role":(HUD,MAP.replace("v.pulse.serverVerified == true","v.pulse.serverVerified ~= true")),
        "fog":(HUD,MAP.replace("m.serverLineOfSight == true and m.stealthed ~= true","m.serverLineOfSight ~= true and m.stealthed ~= true")),
    }
    for name,(h,m) in changes.items():
        assert h!=HUD or m!=MAP,name
        (args.out/(name+"_mutant.luau")).write_text(wrap(h,m),encoding="utf8")
    print("GQ8_HUD_INTEL_ACTUAL_SOURCE_TESTS_GENERATED")

if __name__=="__main__":
    main()
