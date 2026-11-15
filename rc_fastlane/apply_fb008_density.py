#!/usr/bin/env python3
"""FB-008: explicitly isolated real 16+1 server Horde trial, NEVER official RC.

Only swap the verified MusouHorde module in the PRIVATE Studio candidate.
The original 66 file bytes are retained in canonical dist; 65 original sources
and the original Game/Remotes/Store stay byte-identical.
"""
from __future__ import annotations
import hashlib

H = "server/MusouHorde.luau"
ORIGINAL_BLOB = "fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
REPLACEMENTS = (
    ("local MINIONS = 8", "local MINIONS = 16"),
    ("local MAX_ACTIVE = 9", "local MAX_ACTIVE = 17"),
    ("return setmetatable({folder=folder,world=world,mobs={},round=-1,lastTick=0,kills=0},Horde)",
     "return setmetatable({folder=folder,world=world,mobs={},round=-1,lastTick=0,kills=0,tickSequence=0},Horde)"),
    ("    self.kills=0\n    -- Center routes within the original 250x142 arena, NOT remote fantasy scenery.",
     "    self.kills=0\n    self.tickSequence=0\n    -- Center routes within the original 250x142 arena, NOT remote fantasy scenery."),
    (
        "local z=if elite then 0 else (if i<=4 then -18 else 18)",
        "local z=if elite then 0 else (if i<=4 then -18 elseif i<=8 then 18 elseif i<=12 then -6 else 6)",
    ),
    ("    local impacts={}\n    for _,m in ipairs(self.mobs) do",
     "    local impacts={}\n    local minionImpacts=0\n"
     "    local impactsByPlayer={}\n"
     "    -- Circular attack priority: 16 mobs get equal access to the"
     " four-impact fairness cap. Elite still ticks once.\n"
     "    local sweepStart=self.tickSequence%MINIONS\n"
     "    self.tickSequence+=1\n"
     "    for mobIndex=1,#self.mobs do\n"
     "        local slot=if mobIndex<=MINIONS then ((mobIndex-1+sweepStart)%MINIONS)+1 else mobIndex\n"
     "        local m=self.mobs[slot]"),
    (
        "            elseif not m.elite and nearest and now>=m.attackAt\n"
        "                and canStrike(nearest,false) then",
        "            elseif not m.elite and nearest and now>=m.attackAt\n"
        "                and minionImpacts<4 and (impactsByPlayer[nearest] or 0)<2\n"
        "                and canStrike(nearest,false) then",
    ),
    (
        "            if nearest and nearestDist>4.5 and m.tellUntil==0 then",
        "            if nearest and m.tellUntil==0 then",
    ),
    (
        "                    local unit=horizontal(m.pos,root.Position)\n"
        "                    local step=m.pos+unit*math.min(nearestDist-4.5,dt*(if m.elite then 2.8 else 3.4))\n"
        "                    local nextPos=anchoredToWalkable(self.world,m,step)\n"
        "                    if (nextPos-m.home).Magnitude<22 then",
        "                    local unit=horizontal(m.pos,root.Position)\n"
        "                    -- Crowd stays readable instead of collapsing into one model.\n"
        "                    -- O(16*16) at .5s tick, bounded and no physics ownership.\n"
        "                    local separation=Vector3.zero\n"
        "                    if not m.elite then\n"
        "                        for _,other in ipairs(self.mobs) do\n"
        "                            if other~=m and other.hp>0 then\n"
        "                                local away,gap=horizontal(other.pos,m.pos)\n"
        "                                if gap>.01 and gap<5 then\n"
        "                                    separation+=away*((5-gap)/5)\n"
        "                                end\n"
        "                            end\n"
        "                        end\n"
        "                    end\n"
        "                    local approach=math.min(math.max(0,nearestDist-4.5),\n"
        "                        dt*(if m.elite then 2.8 else 3.4))\n"
        "                    local delta=unit*approach+separation*math.min(dt*1.1,.5)\n"
        "                    local step=m.pos+delta\n"
        "                    local nextPos=anchoredToWalkable(self.world,m,step)\n"
        "                    if (nextPos-m.pos).Magnitude>.05\n"
        "                        and (nextPos-m.home).Magnitude<22 then",
    ),
    (
        '                table.insert(impacts,{player=nearest,damage=3,kind="MINION"})\n'
        '                m.attackAt=now+2.5',
        '                table.insert(impacts,{player=nearest,damage=3,kind="MINION"})\n'
        '                minionImpacts+=1\n'
        '                impactsByPlayer[nearest]=(impactsByPlayer[nearest] or 0)+1\n'
        '                m.attackAt=now+2.5',
    ),
)


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def apply_horde(original: bytes) -> bytes:
    assert gitblob(original) == ORIGINAL_BLOB, "FB008_ORIGINAL_HORDE_EXACT_BLOB_REQUIRED"
    decoded = original.decode("utf8")
    for i, (old, new) in enumerate(REPLACEMENTS):
        assert decoded.count(old) == 1, ("FB008_HORDE_ANCHOR_CHANGED", i)
        decoded = decoded.replace(old, new, 1)
    updated = decoded.encode("utf8")
    assert updated != original
    assert gitblob(updated) != ORIGINAL_BLOB
    assert "local MINIONS = 16" in decoded
    assert "local MAX_ACTIVE = 17" in decoded
    assert "touched<6" in decoded, "KEEP_EXISTING_ATTACK_SWEEP_CAP"
    assert 'minionImpacts<4 and (impactsByPlayer[nearest] or 0)<2' in decoded
    assert 'and canStrike(nearest,false)' in decoded
    assert 'local minionImpacts=0' in decoded
    assert "local sweepStart=self.tickSequence%MINIONS" in decoded
    assert "self.tickSequence+=1" in decoded
    assert "for mobIndex=1,#self.mobs do" in decoded
    assert "local slot=if mobIndex<=MINIONS then ((mobIndex-1+sweepStart)%MINIONS)+1 else mobIndex" in decoded
    assert "self.tickSequence=0" in decoded
    assert "local impactsByPlayer={}" in decoded
    assert "(impactsByPlayer[nearest] or 0)<2" in decoded
    assert "impactsByPlayer[nearest]=(impactsByPlayer[nearest] or 0)+1" in decoded
    assert "local separation=Vector3.zero" in decoded
    assert "if gap>.01 and gap<5 then" in decoded
    assert "local delta=unit*approach+separation*math.min(dt*1.1,.5)" in decoded
    assert "if (nextPos-m.pos).Magnitude>.05" in decoded
    assert "local z=if elite then 0 else (if i<=4 then -18 elseif i<=8 then 18 elseif i<=12 then -6 else 6)" in decoded
    # All original source is preserved except the ten explicitly reviewed
    # substitutions; reject any future unrelated Game/authority edits.
    restored = decoded
    for old, new in reversed(REPLACEMENTS):
        assert restored.count(new) == 1
        restored = restored.replace(new, old, 1)
    assert restored.encode("utf8") == original, "FB008_UNCONTROLLED_HORDE_DIFF"
    return updated
