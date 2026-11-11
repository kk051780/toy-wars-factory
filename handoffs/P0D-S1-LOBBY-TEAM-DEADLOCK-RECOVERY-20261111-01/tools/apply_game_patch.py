#!/usr/bin/env python3
"""Source SHA-locked, out-of-tree only patch for official S1's sole Game.server.luau.

Never edits canonical Game.server.luau in place. The RC owner reviews the output and
merges it in their own branch; this tool does not perform Git operations.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

BASE_GAME_GIT_BLOB = "0f2c34fe25c00e3251b9ca53952b9ec75400f365"
BASE_GAME_COMMIT = "35d7d0525388e885aac8281eff2315a59831e0cf"

REPLACEMENTS = (
    (
        'local MapBuilder = require(script.Parent:WaitForChild("MapBuilder"))\n',
        'local MapBuilder = require(script.Parent:WaitForChild("MapBuilder"))\n'
        'local LobbyTeamRecovery = require(script.Parent:WaitForChild("LobbyTeamRecovery"))\n',
    ),
    (
        'local function assignSpawn(player: Player, character: Model)\n',
        '''-- Only LOBBY may correct team balance; never touch a live round or countdown.
-- This is a small attachment to the existing server controller, not another authority.
local function rebalanceLobbyTeams()
    if match.phase ~= "LOBBY" then return end
    local online = Players:GetPlayers()
    if #online < Config.MinPlayers then return end
    local roster = {}
    local byUserId = {}
    for _, player in ipairs(online) do
        table.insert(roster, {userId = player.UserId, team = getTeamName(player)})
        byUserId[player.UserId] = player
    end
    local planned = LobbyTeamRecovery.plan(roster)
    if planned == nil then return end
    for _, move in ipairs(planned) do
        local player = byUserId[move.userId]
        if player and player.Parent == Players and getTeamName(player) == move.from then
            -- Defensive cleanup: no carried egg survives a lobby team move.
            dropEgg(player)
            player.Team = teamInstances[move.to]
            player.Neutral = false
            local alive, root = healthy(player)
            if alive and root then
                root.CFrame = map.teams[move.to].spawn + Vector3.new(0, 2, 0)
            end
        end
    end
end

local function assignSpawn(player: Player, character: Model)
''',
    ),
    (
        '    if match.phase == "LOBBY" then\n'
        '        if count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0 then\n',
        '    if match.phase == "LOBBY" then\n'
        '        rebalanceLobbyTeams()\n'
        '        if count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0 then\n',
    ),
    (
        '    elseif match.phase == "COUNTDOWN" then\n'
        '        if count < Config.MinPlayers then match.phase = "LOBBY"\n'
        '        elseif now >= match.phaseUntil then resetRound() end\n',
        '    elseif match.phase == "COUNTDOWN" then\n'
        '        -- Players can leave during countdown; do not start a one-sided game.\n'
        '        if count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0 then\n'
        '            match.phase = "LOBBY"\n'
        '        elseif now >= match.phaseUntil then resetRound() end\n',
    ),
)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def transform_source(content: str) -> str:
    """Text-only deterministic transformation. CLI enforces the exact original hash."""
    for old, new in REPLACEMENTS:
        if content.count(old) != 1:
            raise ValueError(f"PATTERN_NOT_EXACTLY_ONCE: {old[:72]!r}")
        content = content.replace(old, new, 1)
    return content


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True, help="Immutable baseline Game.server.luau")
    p.add_argument("--output", type=Path, required=True, help="NEW out-of-tree patched file")
    args = p.parse_args()
    source = args.source.resolve()
    dest = args.output.resolve()
    if source == dest or dest.exists() or source.name != "Game.server.luau":
        raise SystemExit("REFUSE_INPLACE_OR_EXISTING_OUTPUT")
    raw = source.read_bytes()
    actual = git_blob_sha(raw)
    if actual != BASE_GAME_GIT_BLOB:
        raise SystemExit(f"BASELINE_SOURCE_SHA_MISMATCH: expected {BASE_GAME_GIT_BLOB}, got {actual}")
    new = transform_source(raw.decode("utf-8")).encode("utf-8")
    if new == raw:
        raise SystemExit("NO_CHANGE")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(new)
    print("PATCHED_OUT_OF_TREE", dest, "inputGitBlob", actual, "outputGitBlob", git_blob_sha(new))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
