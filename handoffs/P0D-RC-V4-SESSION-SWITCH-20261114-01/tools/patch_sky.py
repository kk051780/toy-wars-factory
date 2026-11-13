"""Source-locked BOOT-ONLY H1 Sky V5 switch; no original Game/Store edits."""
from __future__ import annotations
import hashlib

ORIGINAL_BLOB = "7a90affd4eb7eebcdfba39d833a2875ff665d5cf"
FEATURE = "P0D_RC_ENABLE_H1_SKYV5"

def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def once(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise ValueError(f"LOCKED_SKY_ANCHOR_DRIFT:{n} {old[:48]!r}")
    return text.replace(old, new)

def transform(original: bytes) -> bytes:
    if gitblob(original) != ORIGINAL_BLOB:
        raise ValueError("ORIGINAL_H1_WORLD_SOURCE_DRIFT")
    s = original.decode("utf8")
    s = once(s, 'local RunService=game:GetService("RunService")', '''local RunService=game:GetService("RunService")
local ServerStorage=game:GetService("ServerStorage")
-- Sole server configures this before Studio Play. Default ON; NEVER remove
-- solid sky platforms mid-round while a player carries an egg.
local skyEnabled=ServerStorage:GetAttribute("P0D_RC_ENABLE_H1_SKYV5")~=false''')
    s = once(s, "world.Parent=arena", '''world.Parent=arena
world:SetAttribute("H1SkyV5EnabledAtStartup",skyEnabled)''')
    s = once(s, 'path("SKY_RAMP_RED",', 'if skyEnabled then\npath("SKY_RAMP_RED",')
    s = once(s, 'local sea=box("COSMETIC_SEA",',
             'end -- early SKY_RAMP/WALKWAY parts only\nlocal sea=box("COSMETIC_SEA",')
    s = once(s, '-- Ground-dock V5: real low entry/exit ramps,',
             'if skyEnabled then\n-- Ground-dock V5: real low entry/exit ramps,')
    s = once(s, '-- EXACT original #232 moving noncombat model implementation,',
             'end -- late SKY_GROUND_DOCK / SKY_FORT / CLOUDS only\n-- EXACT original #232 moving noncombat model implementation,')
    if s.count("if skyEnabled then") != 2:
        raise ValueError("SKY_GUARD_INCOMPLETE")
    if s.count("SKY_FORT_ESCAPE_BLUE") != 1 or "SEA_LOW_CAUSEWAY" not in s:
        raise ValueError("ROUTE_DRIFT")
    if FEATURE not in s:
        raise ValueError("SKY_FLAG_MISSING")
    return s.encode("utf8")
