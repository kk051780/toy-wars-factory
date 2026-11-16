#!/usr/bin/env python3
"""Execute original #482 BOSS credit statements AND original Replay.resetHuman,
joined to #514's ACTUAL server observer. This changes no original game source.

The harness imports the existing 18-case mock observer generator, then appends
two exact source excerpts copied from the immutable original author. It runs
in two explicit native-Luau service settings: Studio and live-like server.
It is NOT Roblox Studio or a real multiplayer server.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPLAY = HERE.parents[1] / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116" / "EGGRUMBLE_RoundReplay.luau"
LOBBY = HERE.parents[1] / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116" / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"

def build(output: Path, runtime: str) -> None:
    assert runtime in ("studio", "live-server"), "explicit server context required"
    replay = REPLAY.read_text(encoding="utf-8")
    lobby = LOBBY.read_text(encoding="utf-8")
    start = "function Replay.resetHuman("
    stop = "\nend\n\nreturn Replay"
    assert replay.count(start) == 1, "original replay method changed, review needed"
    assert replay.count(stop) == 1, "original replay method ending changed, review needed"
    original_function = replay[replay.index(start):replay.index(stop, replay.index(start)) + len("\nend")]
    assert original_function.count('p:SetAttribute("EGGRUMBLE_QueuedMode",nil)') == 1
    assert "EGGRUMBLE_BossDefeats" not in original_function, "original author already fixed; remove overlay"

    # Source-exact boss award statements from original real onDefeat callback.
    award_pattern = re.compile(
        r'local total=player:GetAttribute\("EGGRUMBLE_BossDefeats"\) or 0'
        r'\s+player:SetAttribute\("EGGRUMBLE_BossDefeats",total\+1\)'
    )
    credits = award_pattern.findall(lobby)
    assert len(credits) == 1, "original source award drift"
    award = credits[0]

    with tempfile.TemporaryDirectory(prefix="gq514-replay-") as tmp:
        base = Path(tmp) / "existing_observer.luau"
        subprocess.run(
            [sys.executable, str(HERE / "make_native_observer_harness.py"),
             str(base), runtime], check=True, capture_output=True, text=True)
        mock_and_observer = base.read_text(encoding="utf-8")

    integration = r"""
-- These two blocks are original-author code, included exactly at author SHA.
local Replay={}
""" + original_function + r"""

local function originalBossAward(player)
""" + award + r"""
end

local replayChecks=0
local function verifyReplay(value, label)
    assert(value, "ORIGINAL_REPLAY_BRIDGE: " .. label)
    replayChecks+=1
end
local function originalPlayer(id, mode, initialKO)
    local player=makePlayer(id,mode,initialKO)
    player.reloads=0
    function player:FindFirstChild(name)
        assert(name=="leaderstats", "unexpected child requested by real author replay")
        return nil
    end
    function player:LoadCharacter()
        self.reloads+=1
    end
    Players.PlayerAdded:Fire(player)
    return player
end

local teamPlayer=originalPlayer(204,"TEAM",0)
verifyReplay(teamPlayer:GetAttribute(COUNTER)==0, "new TEAM starts without boss KO")
originalBossAward(teamPlayer)
verifyReplay(teamPlayer:GetAttribute(COUNTER)==1, "original callback awards first real BOSS KO")
originalBossAward(teamPlayer)
verifyReplay(teamPlayer:GetAttribute(COUNTER)==2, "original callback awards multiple BOSS KOs")
Replay.resetHuman(teamPlayer,nil,nil)
verifyReplay(teamPlayer:GetAttribute(COUNTER)==0, "ORIGINAL RoundReplay.resetHuman fires boss clear")
verifyReplay(teamPlayer:GetAttribute(MODE)==nil, "ORIGINAL RoundReplay resets server queued mode")
verifyReplay(teamPlayer.reloads==1, "original reset took valid LoadCharacter path")
teamPlayer:SetAttribute(MODE,"BATTLE_ROYALE")
verifyReplay(teamPlayer:GetAttribute(COUNTER)==0, "fresh BR after genuine original TEAM cleanup")
originalBossAward(teamPlayer)
verifyReplay(teamPlayer:GetAttribute(COUNTER)==1, "BR BOSS KO counts again normally")
local brPlayer=originalPlayer(205,"BATTLE_ROYALE",5)
verifyReplay(brPlayer:GetAttribute(COUNTER)==5, "late join bind never erases in-progress BR count")
originalBossAward(brPlayer)
verifyReplay(brPlayer:GetAttribute(COUNTER)==6, "original boss credit not blocked by observer")
verifyReplay(teamPlayer:GetAttribute(COUNTER)==1, "other player BOSS KO is isolated")
Replay.resetHuman(brPlayer,nil,nil)
verifyReplay(brPlayer:GetAttribute(COUNTER)==0, "original BR cleanup clears its boss count")
verifyReplay(teamPlayer:GetAttribute(COUNTER)==1, "original BR cleanup doesn't touch other human")
teamPlayer:SetAttribute(MODE,nil)
verifyReplay(teamPlayer:GetAttribute(COUNTER)==0, "true BR-to-lobby boundary clears KO")
originalBossAward(teamPlayer)
verifyReplay(teamPlayer:GetAttribute(COUNTER)==1, "lobby has no new protection authority; source-only counter")
teamPlayer:SetAttribute(MODE,"TEAM")
verifyReplay(teamPlayer:GetAttribute(COUNTER)==0, "lobby-to-new-TEAM reinitializes counter")
verifyReplay(replayChecks==16, "regression count drift")
print("BOSS_CREDIT_ORIGINAL_AUTHOR_REPLAY_" ..
      (SIMULATED_STUDIO and "STUDIO" or "LIVE_SERVER_LIKE") ..
      ": 16/16 PASS")
"""
    output.write_text(mock_and_observer + "\n" + integration, encoding="utf-8")
    print(output)

if __name__=="__main__":
    assert len(sys.argv) == 3, "usage: script.py generated.luau studio|live-server"
    build(Path(sys.argv[1]), sys.argv[2])
