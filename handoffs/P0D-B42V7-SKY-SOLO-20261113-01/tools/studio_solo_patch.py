#!/usr/bin/env python3
"""Only a Studio-local, real ONE-human solo trial; NEVER live/public.
Input: exact B42/V7/SkyCastle Game.server.luau from immutable a3dfc9b source.
Output: patched Game in an isolated copied game. Fail closed on any source drift.
"""
from pathlib import Path
import hashlib
import sys

EXPECTED_OLD_SHA256 = "81bc7a05ec0ab613c61f6030966dfeae7eab0c04122325f2a50eadf512d1a9c2"
EXPECTED_NEW_SHA256 = "4b17afecb16bb1c394603eae5bb17d7dac354ee0ade7e5dc16d3a3b8383b24f2"

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def once(s:str,old:str,new:str)->str:
    if s.count(old)!=1:
        raise ValueError("Source marker drift: "+old[:100])
    return s.replace(old,new,1)

def patch_game(source:str)->str:
    s=source
    s=once(s,'-- Only the ORIGINAL Game.server owns the H2 match, egg interactions and scoring.',
        'local studioSoloRound = false -- latched only at authoritative round start\n'
        '-- Only the ORIGINAL Game.server owns the H2 match, egg interactions and scoring.')
    s=once(s,'-- ONLY Server Game confirms objective events.',
'''-- Private Studio local preview only. The published/live game always requires BOTH teams.
-- This checks a real Player on one already assigned original team; never fakes users.
local function isStudioSoloPlayer(): boolean
    if not RunService:IsStudio() then return false end
    local online = Players:GetPlayers()
    if #online ~= 1 then return false end
    local t = getTeamName(online[1])
    return t == "RED" or t == "BLUE"
end

-- ONLY Server Game confirms objective events.''')
    s=once(s,'''local function resetRound()
    stopCanonical("ROUND_RESET")''',
       '''local function resetRound()
    studioSoloRound = isStudioSoloPlayer() -- match-scoped; never allows a 2-player disconnect exploit
    stopCanonical("ROUND_RESET")''')
    s=once(s,
       '''if count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0 then''',
       '''if (count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0)
            or isStudioSoloPlayer() then''')
    s=once(s,
       '''if count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0 then
            match.phase = "LOBBY"''',
       '''if not isStudioSoloPlayer() and
            (count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0) then
            match.phase = "LOBBY"''')
    s=once(s,
       '''if teamCount("RED") <= 0 then stopRound("BLUE", "TEAM_EMPTY")
        elseif teamCount("BLUE") <= 0 then stopRound("RED", "TEAM_EMPTY")''',
       '''local activePrivateSolo = studioSoloRound and isStudioSoloPlayer()
        if teamCount("RED") <= 0 and not activePrivateSolo then stopRound("BLUE", "TEAM_EMPTY")
        elseif teamCount("BLUE") <= 0 and not activePrivateSolo then stopRound("RED", "TEAM_EMPTY")''')
    return s

def main():
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python studio_solo_patch.py exact_original_Game.server.luau")
    file=Path(sys.argv[1])
    old=file.read_bytes()
    if sha(old)!=EXPECTED_OLD_SHA256:
        raise ValueError("Original source SHA256 drift: will NOT patch")
    new=patch_game(old.decode("utf-8")).encode("utf-8")
    if sha(new)!=EXPECTED_NEW_SHA256:
        raise ValueError("Replacement source differs from original local tested program")
    file.write_bytes(new)
    print("P0D_B42_V7_SKY_SOLO_ONE_GAME_ORIGINAL_SHA_LOCK_PASS")

if __name__=="__main__":main()
