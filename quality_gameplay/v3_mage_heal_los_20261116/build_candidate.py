#!/usr/bin/env python3
"""SHA-locked, single-owner source patch: MAGE ally-heal LOS in EGGRUMBLE V3.

The original #482 SevenRoleCombat.luau is never modified. A patched candidate is
written only to a scratch output path for native VM tests and RC-author review.
"""
import argparse
import difflib
import hashlib
from pathlib import Path

SOURCE = Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SevenRoleCombat.luau")
SOURCE_BLOB = "66e666418b7c23d41f87faa5d61eb6e2770a463e"
ORIGINAL_HEAD = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"

OLD_GUARD = '''local function healAllies(session:any,player:Player,root:BasePart)
 local state=session.rules.castles[tostring(player.UserId)]
 if not state then return end
 for _,other in ipairs(game:GetService("Players"):GetPlayers()) do'''
NEW_GUARD = '''local function healAllies(session:any,player:Player,root:BasePart)
 local state=session.rules.castles[tostring(player.UserId)]
 local sourceCharacter=player.Character
 if not state or not state.alive or not sourceCharacter then return end
 for _,other in ipairs(game:GetService("Players"):GetPlayers()) do'''
OLD_RANGE = '''   and (otherRoot.Position-root.Position).Magnitude<=22 then
   h.Health=math.min(h.MaxHealth,h.Health+25)'''
NEW_RANGE = '''   and (otherRoot.Position-root.Position).Magnitude<=22
   and (other==player or lineClear(root.Position+Vector3.new(0,1.5,0),
    otherRoot.Position+Vector3.new(0,1,0),sourceCharacter,char)) then
   h.Health=math.min(h.MaxHealth,h.Health+25)'''

BOT_TAIL = '''  end
 end
end
-- Status effects are real server damage / movement changes (not only colored VFX).'''
BOT_HEAL = '''  end
 end
 -- Team support must also serve existing server-owned companion AI.
 -- No extra healer, Remote, Game or score authority; keep BR strictly self-only.
 if session.mode=="TEAM" then
  for id,bot in pairs(session.botActors or {}) do
   local teammate=session.rules.castles[id]
   local botRoot=bot and bot.PrimaryPart
   local botHum=bot and bot:FindFirstChildOfClass("Humanoid")
   if teammate and teammate.alive and teammate.team==state.team
    and bot and bot.Parent and botRoot and botHum and botHum.Health>0
    and (botRoot.Position-root.Position).Magnitude<=22
    and lineClear(root.Position+Vector3.new(0,1.5,0),
     botRoot.Position+Vector3.new(0,1,0),sourceCharacter,bot) then
    botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)
   end
  end
 end
end
-- Status effects are real server damage / movement changes (not only colored VFX).'''

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def source_function(source: str, beginning: str, ending: str) -> str:
    assert source.count(beginning) == 1 and source.count(ending) == 1
    return beginning + source.split(beginning, 1)[1].split(ending, 1)[0] + "\nend\n"

def patch(source: str) -> str:
    for old in (OLD_GUARD, OLD_RANGE):
        if source.count(old) != 1:
            raise AssertionError("author source drift; abort instead of applying fuzzy patch")
    if source.count("local function lineClear(") != 1:
        raise AssertionError("cannot reuse original LOS authority")
    if source.count(BOT_TAIL) != 1:
        raise AssertionError("author heal function tail drift; abort")
    changed = source.replace(OLD_GUARD, NEW_GUARD).replace(OLD_RANGE, NEW_RANGE)
    changed = changed.replace(BOT_TAIL, BOT_HEAL)
    assert changed != source
    assert changed.count('h.Health=math.min(h.MaxHealth,h.Health+25)') == 1
    assert changed.count('botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)') == 1
    # No damage, cooldown, target mode, neutral, castle, AI, item, lobby edits.
    assert changed.count("function HeroCombat.equip") == source.count("function HeroCombat.equip")
    return changed

def harness(src: str, *, fixed: bool) -> str:
    los = source_function(src, "local function lineClear(", "\nend\nlocal function hitBotHeroes")
    heal = source_function(src, "local function healAllies(", "\nend\n-- Status effects")
    test = r'''
local mt={}
mt.__index=function(v,k)
 if k=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
 return rawget(v,k)
end
mt.__add=function(a,b) return setmetatable({X=a.X+b.X,Y=a.Y+b.Y,Z=a.Z+b.Z},mt) end
mt.__sub=function(a,b) return setmetatable({X=a.X-b.X,Y=a.Y-b.Y,Z=a.Z-b.Z},mt) end
local function v(x,y,z) return setmetatable({X=x,Y=y,Z=z},mt) end
Vector3={new=v}
RaycastParams={new=function() return {} end}
Enum={RaycastFilterType={Exclude="EXCLUDE"}}
local blocked=false
local rays=0
workspace={Raycast=function(_,a,b,options)
 rays+=1
 assert(options.RespectCanCollide==true, "healing LOS must respect walls")
 return if blocked then {Instance={}} else nil
end}
local source={UserId=1,Character={tag="source"},root={Position=v(0,0,0)},h={Health=65,MaxHealth=100}}
local ally={UserId=2,Character={tag="ally"},root={Position=v(8,0,0)},h={Health=60,MaxHealth=100}}
local enemy={UserId=3,Character={tag="enemy"},root={Position=v(7,0,0)},h={Health=60,MaxHealth=100}}
local far={UserId=4,Character={tag="far"},root={Position=v(30,0,0)},h={Health=60,MaxHealth=100}}
local people={source,ally,enemy,far}
local game={GetService=function(_,name)
 assert(name=="Players");return {GetPlayers=function() return people end}
end}
local function characterOf(p)
 if not p.Character or p.h.Health<=0 then return nil,nil,nil end
 return p.Character,p.root,p.h
end
local session={mode="TEAM",rules={castles={
 ["1"]={team="RED",alive=true},["2"]={team="RED",alive=true},
 ["3"]={team="BLUE",alive=true},["4"]={team="RED",alive=true},
 ["AI_1"]={team="RED",alive=true},["AI_2"]={team="BLUE",alive=true},
 ["AI_3"]={team="RED",alive=true},["AI_4"]={team="RED",alive=true}
}}}
local function mkbot(x,hp)
 local bot={Parent=true,PrimaryPart={Position=v(x,0,0)},hum={Health=hp,MaxHealth=100}}
 function bot:FindFirstChildOfClass(name)
  assert(name=="Humanoid")
  return self.hum
 end
 return bot
end
local goodBot=mkbot(8,50)
local enemyBot=mkbot(6,50)
local farBot=mkbot(28,50)
local deadBot=mkbot(7,0)
session.botActors={AI_1=goodBot,AI_2=enemyBot,AI_3=farBot,AI_4=deadBot}
'''
    cases = r'''
-- 1. Source heal and ally: a solid wall cannot be bypassed.
blocked=true
healAllies(session,source,source.root)
assert(source.h.Health==90, "self heal must not be blocked by own wall")
assert(ally.h.Health==EXPECTED_WALL_HEALTH, "wall-heal behavior changed unexpectedly")
assert(enemy.h.Health==60, "enemy heal prohibited")
assert(far.h.Health==60, "out-of-range heal prohibited")
if FIXED then assert(rays>=1, "must actually use original wall raycast") end

-- 2. Clear path permits an ally's 25HP recovery; heal is capped at max health.
blocked=false; ally.h.Health=85;source.h.Health=95; rays=0
healAllies(session,source,source.root)
assert(ally.h.Health==100 and source.h.Health==100,"unblocked heal / HP cap")

-- 3. TEAM friendly only, even when same location.
enemy.root.Position=v(3,0,0);enemy.h.Health=20
healAllies(session,source,source.root)
assert(enemy.h.Health==20, "friendly-fire team ownership invariant")

-- 4. Eliminated source cannot heal, even if role tool callback survived.
if FIXED then
 session.rules.castles["1"].alive=false
 ally.h.Health=25
 healAllies(session,source,source.root)
 assert(ally.h.Health==25,"eliminated caster must never heal")
 session.rules.castles["1"].alive=true
end

-- 5. BR mode heals self, but no other player even when same approximate team tag.
session.mode="BATTLE_ROYALE"
source.h.Health=55;ally.h.Health=60
healAllies(session,source,source.root)
assert(source.h.Health==80 and ally.h.Health==60,"BR self only")

-- 6. No source avatar means no post-respawn heal from the old tool callback.
if FIXED then
 session.mode="TEAM"
 source.Character=nil
 source.h.Health=55;ally.h.Health=60
 healAllies(session,source,source.root)
 assert(source.h.Health==55 and ally.h.Health==60,"stale actor must not heal")
end
-- 7. Existing teammate bots share the original MAGE heal in TEAM only.
if FIXED then
 source.Character={tag="source"}
 source.h.Health=100;ally.h.Health=100
 session.mode="TEAM"
 blocked=true;goodBot.hum.Health=50;enemyBot.hum.Health=50
 healAllies(session,source,source.root)
 assert(goodBot.hum.Health==50,"blocked AI teammate must not heal")
 blocked=false
 healAllies(session,source,source.root)
 assert(goodBot.hum.Health==75,"unblocked TEAM AI should receive exact +25")
 assert(enemyBot.hum.Health==50,"enemy bot cannot receive opponent heal")
 assert(farBot.hum.Health==50 and deadBot.hum.Health==0,
  "out-of-range or dead AI bot healed")
 -- 8. BR is always self-only, even if old TEAM bot state lingers.
 session.mode="BATTLE_ROYALE"
 goodBot.hum.Health=55
 healAllies(session,source,source.root)
 assert(goodBot.hum.Health==55,"BR may not heal TEAM bots")
 -- 9. Eliminated / despawned team AI never benefits from MAGE support.
 session.mode="TEAM"
 session.rules.castles["AI_1"].alive=false
 healAllies(session,source,source.root)
 assert(goodBot.hum.Health==55,"fallen castle bot must not heal")
 session.rules.castles["AI_1"].alive=true
 goodBot.Parent=nil
 healAllies(session,source,source.root)
 assert(goodBot.hum.Health==55,"destroyed AI model must not heal")
 goodBot.Parent=true
 -- 10. HP caps apply to teammate AI as to human allies.
 goodBot.hum.Health=95
 healAllies(session,source,source.root)
 assert(goodBot.hum.Health==100,"AI heal must cap at maximum")
 print("MAGE_TEAM_BOT_HEAL_NATIVE_VM_CASES_PASS")
end
print("MAGE_HEAL_LOS_NATIVE_VM_CASES_PASS",FIXED and "FIXED" or "ORIGINAL_BUG_REPRODUCED")
'''
    header = f"local FIXED={'true' if fixed else 'false'}\nlocal EXPECTED_WALL_HEALTH={60 if fixed else 85}\n"
    return header + test + "\n" + los + "\n" + heal + "\n" + cases

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patched", type=Path, required=True)
    ap.add_argument("--harness", type=Path, required=True)
    ap.add_argument("--original-harness", type=Path, required=True)
    args = ap.parse_args()
    raw = SOURCE.read_bytes()
    assert git_blob(raw) == SOURCE_BLOB, "original #482 Luau blob drift: fail-closed"
    before = raw.decode("utf-8")
    after = patch(before)
    diff = list(difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm=""))
    added = sum(line.startswith("+") and not line.startswith("+++") for line in diff)
    removed = sum(line.startswith("-") and not line.startswith("---") for line in diff)
    assert added == 23 and removed == 2, (added, removed, diff)
    for path, text in ((args.patched, after),
                       (args.harness, harness(after, fixed=True)),
                       (args.original_harness, harness(before, fixed=False))):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print("OWNER_BLOB_PIN", SOURCE_BLOB)
    print("MAGE_HEAL_MINIMAL_PATCH_PASS", f"added={added}", f"deleted={removed}")
    print("ORIGINAL_AUTHOR_SCRIPT_UNMODIFIED", SOURCE)

if __name__ == "__main__":
    main()
