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
        "                and minionImpacts<4 and canStrike(nearest,false) then",
    ),
    (
        '                table.insert(impacts,{player=nearest,damage=3,kind="MINION"})\n'
        '                m.attackAt=now+2.5',
        '                table.insert(impacts,{player=nearest,damage=3,kind="MINION"})\n'
        '                minionImpacts+=1\n'
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
    assert 'minionImpacts<4 and canStrike(nearest,false)' in decoded
    assert 'local minionImpacts=0' in decoded
    assert "local sweepStart=self.tickSequence%MINIONS" in decoded
    assert "self.tickSequence+=1" in decoded
    assert "for mobIndex=1,#self.mobs do" in decoded
    assert "local slot=if mobIndex<=MINIONS then ((mobIndex-1+sweepStart)%MINIONS)+1 else mobIndex" in decoded
    assert "self.tickSequence=0" in decoded
    assert "local z=if elite then 0 else (if i<=4 then -18 elseif i<=8 then 18 elseif i<=12 then -6 else 6)" in decoded
    # All original source is preserved except the six explicitly reviewed
    # substitutions; reject any future unrelated Game/authority edits.
    restored = decoded
    for old, new in reversed(REPLACEMENTS):
        assert restored.count(new) == 1
        restored = restored.replace(new, old, 1)
    assert restored.encode("utf8") == original, "FB008_UNCONTROLLED_HORDE_DIFF"
    return updated
