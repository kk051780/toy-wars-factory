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

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def source_function(source: str, beginning: str, ending: str) -> str:
    assert source.count(beginning) == 1 and source.count(ending) == 1
    return source.split(beginning, 1)[1].split(ending, 1)[0].join([]) if False else (
        beginning + source.split(beginning, 1)[1].split(ending, 1)[0] + "\nend\n"
    )

def patch(source: str) -> str:
    for old in (OLD_GUARD, OLD_RANGE):
        if source.count(old) != 1:
            raise AssertionError("author source drift; abort instead of applying fuzzy patch")
    if source.count("local function lineClear(") != 1:
        raise AssertionError("cannot reuse original LOS authority")
    changed = source.replace(OLD_GUARD, NEW_GUARD).replace(OLD_RANGE, NEW_RANGE)
    assert changed != source
    assert changed.count('h.Health=math.min(h.MaxHealth,h.Health+25)') == 1
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
 ["3"]={team="BLUE",alive=true},["4"]={team="RED",alive=true}
}}}
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
    assert sum(line.startswith("+") and not line.startswith("+++") for line in diff) == 5, diff
    assert sum(line.startswith("-") and not line.startswith("---") for line in diff) == 2, diff
    for path, text in ((args.patched, after),
                       (args.harness, harness(after, fixed=True)),
                       (args.original_harness, harness(before, fixed=False))):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print("OWNER_BLOB_PIN", SOURCE_BLOB)
    print("MAGE_HEAL_MINIMAL_PATCH_PASS", "added=5", "deleted=2")
    print("ORIGINAL_AUTHOR_SCRIPT_UNMODIFIED", SOURCE)

if __name__ == "__main__":
    main()
