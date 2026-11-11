#!/usr/bin/env python3
"""Source-pinned, read-only S1 authority regression gate. No Roblox runtime claims."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys

PIN = "b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc"
ROOT = "handoffs/P0D-S1-FTUE-ON-D07D08-SPATIAL-LOBBY-20261112-01/candidate/src/server"
BLOBS = {
    "Game.server.luau": "3d3c5934e110099517fc4a7eb5aa914fcd52f145",
    "S1Rules.luau": "5652b5b43d753c2fcbd27b6c040a34a3642f71ee",
    "GoroganDamageBoundary.luau": "031b0c4a5370a891434de42ada8d76642c080433",
    "GoroganAttackReceiptWindow.luau": "bc8e4e954c06c1db8778649a84cda135ff56e9d1",
}

def load_source(repo: str) -> dict[str, str]:
    out = {}
    for name, expected in BLOBS.items():
        path = f"{PIN}:{ROOT}/{name}"
        result = subprocess.run(
            ["git", "-C", repo, "show", path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if result.returncode:
            raise RuntimeError(f"MISSING_PINNED_SOURCE {name}: {result.stderr.decode(errors='replace')[:250]}")
        b = result.stdout
        blob = hashlib.sha1(b"blob " + str(len(b)).encode("ascii") + b"\0" + b).hexdigest()
        if blob != expected:
            raise RuntimeError(f"BLOB_MISMATCH {name}: {blob} != {expected}")
        out[name] = b.decode("utf-8")
    return out

def controls(files: dict[str, str]) -> dict[str, bool]:
    g = files["Game.server.luau"]
    r = files["S1Rules.luau"]
    d = files["GoroganDamageBoundary.luau"]
    w = files["GoroganAttackReceiptWindow.luau"]
    return {
        "single_server_remote_listener": g.count("remote.OnServerEvent:Connect(") == 1,
        "whitelisted_client_actions": 'if data.action == "ATTACK" then applyAttack(player, data)' in g
            and 'elseif data.action == "ROLE" then applyRole(player, data)' in g
            and not any(f"data.{k}" in g for k in ("damage", "hp", "winner", "target", "score", "position")),
        "authenticated_player_from_server_event":
            "remote.OnServerEvent:Connect(function(player: Player, data)" in g,
        "monotonic_clamped_sequence":
            "seq > previous and seq >= 1 and seq <= 1000000000" in r,
        "sequence_guard_both_actions":
            g.count("Rules.validSeq(data.seq, lastSeq[player] or 0)") == 2,
        "server_attack_cooldown":
            "Rules.canAttack(now, lastAttack[player] or -math.huge" in g,
        "egg_score_requires_true_carrier":
            "if not stolenTeam or match.eggOwners[stolenTeam] ~= player then return end" in g,
        "egg_score_requires_own_egg":
            "carriedEggTeam == Rules.opponent(team) and ownEggAtBase" in r,
        "egg_steal_server_geometry":
            "within(player, map.teams[team].egg.Position, Config.InteractDistance)" in g,
        "castle_damage_raycast_occlusion":
            "local hit = workspace:Raycast(root.Position, core.Position - root.Position, params)" in g
            and "if hit and hit.Instance ~= core then return end" in g,
        "melee_raycast_occlusion":
            "local hit = workspace:Raycast(root.Position, displacement, params)" in g
            and "hit.Instance:IsDescendantOf(other.Character)" in g,
        "boss_explicit_approval":
            "deps.integrationApproved==true" in d,
        "boss_real_round_context":
            "self.deps.isRealRoundEvent(roundId,eventId)~=true" in d,
        "boss_canonical_attack_receipt":
            "self.deps.isCanonicalAttackReceipt(roundId,eventId,attackId)~=true" in d,
        "boss_receipt_once_per_player":
            'if self.receipts[key] then return false,"DUPLICATE_DAMAGE" end' in d,
        "boss_safezone_and_immunity":
            "self.deps.isSafeZone(player)~=false or self.deps.isDamageImmune(player)~=false" in d,
        "boss_server_los_raycast":
            "workspace:Raycast(origin,direction,params)" in d,
        "boss_core_stomp_resolve_attestation":
            'cmd.kind~="STOMP_RESOLVE"' in w,
        "boss_release_review_flags_off":
            "CANONICAL_S1_ENABLED = false" in g
            and "D07_D08_RELEASE_REVIEW_APPROVED = false" in g,
    }

MUTANTS = [
    ("replayed_attack_seq", "S1Rules.luau",
     "seq > previous and seq >= 1", "seq >= previous and seq >= 1",
     "monotonic_clamped_sequence"),
    ("extra_client_action", "Game.server.luau",
     'elseif data.action == "ROLE" then applyRole(player, data)',
     'elseif data.action == "ROLE" then applyRole(player, data.damage)',
     "whitelisted_client_actions"),
    ("carried_egg_owner_bypass", "Game.server.luau",
     "if not stolenTeam or match.eggOwners[stolenTeam] ~= player then return end",
     "if not stolenTeam then return end", "egg_score_requires_true_carrier"),
    ("castle_wall_bypass", "Game.server.luau",
     "if hit and hit.Instance ~= core then return end",
     "if false then return end", "castle_damage_raycast_occlusion"),
    ("boss_attestation_removed", "GoroganDamageBoundary.luau",
     "self.deps.isCanonicalAttackReceipt(roundId,eventId,attackId)~=true",
     "false", "boss_canonical_attack_receipt"),
    ("boss_duplicate_damage", "GoroganDamageBoundary.luau",
     'if self.receipts[key] then return false,"DUPLICATE_DAMAGE" end',
     'if false then return false,"DUPLICATE_DAMAGE" end',
     "boss_receipt_once_per_player"),
    ("unapproved_boss_enable", "Game.server.luau",
     "D07_D08_RELEASE_REVIEW_APPROVED = false",
     "D07_D08_RELEASE_REVIEW_APPROVED = true",
     "boss_release_review_flags_off"),
    ("boss_unchecked_los", "GoroganDamageBoundary.luau",
     "workspace:Raycast(origin,direction,params)",
     "nil -- removed raycast",
     "boss_server_los_raycast"),
]

def run(repo: str) -> int:
    files = load_source(repo)
    report = controls(files)
    mutation_results = {}
    for label, filename, old, new, expected_failure in MUTANTS:
        if files[filename].count(old) != 1:
            mutation_results[label] = "INVALID_MUTATION_SITE"
            continue
        modified = dict(files)
        modified[filename] = files[filename].replace(old, new, 1)
        mutation_results[label] = "REJECTED" if not controls(modified)[expected_failure] else "MISSED"
    passed = all(report.values())
    rejected = all(v == "REJECTED" for v in mutation_results.values())
    output = {
        "game_id": "TRAP_RAIDERS",
        "candidate_sha": PIN,
        "level": "SOURCE_STATIC_ONLY_NOT_LUAU_RUNTIME_NOT_STUDIO",
        "checks": report, "checks_passed": sum(report.values()),
        "checks_total": len(report),
        "mutations": mutation_results,
        "mutations_rejected": sum(v == "REJECTED" for v in mutation_results.values()),
        "mutations_total": len(mutation_results),
        "result": "PASS_SOURCE_STATIC" if passed and rejected else "FAIL_CLOSED",
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if passed and rejected else 1

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="local Git checkout containing pinned candidate commit")
    args = parser.parse_args()
    try:
        return run(args.repo)
    except (RuntimeError, UnicodeError, OSError) as exc:
        print(json.dumps({"result": "BLOCKED_FAIL_CLOSED", "error": str(exc)}))
        return 2

if __name__ == "__main__":
    sys.exit(main())
