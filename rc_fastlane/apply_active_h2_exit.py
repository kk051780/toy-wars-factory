"""Apply the existing #397 Studio H2 roster-exit guard to active rich51."""

import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_active_solo_bots import GAME
from apply_core_round_ready import once
from integrate import gitblob, sources


LOCK = Path(__file__).resolve().parent / "features/active_h2_exit/source_lock.json"
CALLBACK = "Players.PlayerRemoving:Connect(function(player)"
REASON = "SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY"
OLD = '    if match.phase == "ACTIVE" and side ~= "NONE" then'
NEW = '''    local activeH2 = match.phase == "ACTIVE" and EXPERIMENTAL_FIVE_EGG_MODE
        and RunService:IsStudio()
    local combatantLeaving = side ~= "NONE"
        and (not activeH2 or player:GetAttribute("P0D_LateJoinSpectator") ~= true)
    if activeH2 and combatantLeaving then
        local survivors=0
        for _,remaining in ipairs(eligibleSoloPlayers()) do
            if remaining~=player then survivors+=1 end
        end
        if survivors==1 then
            stopRound("DRAW","SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY")
        end
    end
    if match.phase == "ACTIVE" and combatantLeaving then'''


def split_callback(source):
    if source.count(CALLBACK) != 1:
        raise ValueError("ACTIVE_H2_EXIT_PLAYER_REMOVING_ANCHOR")
    prefix, rest = source.split(CALLBACK, 1)
    callback, suffix = rest.split("\nend)\n", 1)
    return prefix, callback, suffix


def patch_game(source):
    prefix, callback, suffix = split_callback(source)
    if REASON in source or 'stopRound(Rules.opponent(side), "OPPONENT_LEFT")' not in callback:
        raise ValueError("ACTIVE_H2_EXIT_ORIGINAL_FORFEIT_REQUIRED")
    return prefix + CALLBACK + once(callback, OLD, NEW) + "\nend)\n" + suffix


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    pinned = json.loads(LOCK.read_bytes())
    enabled = pinned["enabled"] if enabled_override is None else enabled_override
    if type(enabled) is not bool or pinned["profile"] != profile:
        raise ValueError("ACTIVE_H2_EXIT_CONFIG")
    if not enabled:
        return False
    original = sources(dist)
    before = {path: gitblob(raw) for path, raw in original.items()}
    lock_path, features_path = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    lock, features = (json.loads(path.read_bytes()) for path in (lock_path, features_path))
    if (len(before) != lock["total_scripts"] or len(before) != features["total_sources"]
            or before != lock["blobs"] or before != features["source_gitblobs"]
            or lock["rc_active_solo_bots"]["game_after"] != pinned["before"]
            or before[GAME] != pinned["before"]):
        raise ValueError("ACTIVE_H2_EXIT_CURRENT_ACTIVE_DRIFT")
    game = patch_game(original[GAME].decode()).encode()
    if gitblob(game) != pinned["after"]:
        raise ValueError("ACTIVE_H2_EXIT_EXACT_GAME")
    (dist / "src" / GAME).write_bytes(game)
    if sources(dist) != original | {GAME: game}:
        raise ValueError("ACTIVE_H2_EXIT_GAME_ONLY")
    after = before | {GAME: pinned["after"]}
    receipt = {"feature": "GQ910_ACTIVE_H2_DEPARTURE_READY", "studio_score5_only": True,
               "before": pinned["before"], "after": pinned["after"],
               "source": pinned["source"], "studio": "NOT_TESTED_ON_CURRENT_SHA"}
    lock.update(blobs=after, rc_active_h2_exit=receipt)
    features.update(source_gitblobs=after, rc_active_h2_exit=receipt)
    write_json(lock_path, lock)
    write_json(features_path, features)
    print("ACTIVE_RICH51_H2_DEPARTURE_AND_FRESH_READY_EXACT_GAME_ONLY_PASS")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    parser.add_argument("--off-place", type=Path)
    args = parser.parse_args()
    pinned = json.loads(LOCK.read_bytes())
    if args.profile == pinned["profile"] and pinned["enabled"] is True:
        if args.off_place is None:
            parser.error("--off-place is required to prove the exact current rollback")
        raw = args.off_place.read_bytes()
        actual = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        if actual != pinned["off_place"]:
            raise ValueError("ACTIVE_H2_EXIT_OFF_PLACE_MISMATCH")
        print("ACTIVE_RICH51_H2_EXIT_OFF_EXACT", json.dumps(actual))
    apply(args.dist, args.profile)
