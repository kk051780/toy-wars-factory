"""Return the existing FB-019 server-confirmed hit cue in active rich51."""

import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources


PACKAGE = Path(__file__).resolve().parent / "features/active_confirmed_hit"
GAME, HUD, HORDE = "server/Game.server.luau", "client/HUD.client.luau", "server/MusouHorde.luau"
FEATURE = "FB019_ATTACK_RESPONSE_V1"


def check(condition, name):
    if not condition:
        raise ValueError("ACTIVE_CONFIRMED_HIT_" + name)


def apply(dist, profile, enabled_override=None):
    if profile != "rich51":
        return False
    required = json.loads((PACKAGE / "source_lock.json").read_bytes())
    enabled = required["enabled"] if enabled_override is None else enabled_override
    check(type(enabled) is bool and required["profile"] == profile, "CONFIG")
    if not enabled:
        return False
    original = sources(dist)
    identities = {name: gitblob(raw) for name, raw in original.items()}
    lock_path, features_path = dist / "SOURCE_LOCK.json", dist / "RC_FEATURE_LOCK.json"
    lock, features = (json.loads(path.read_bytes()) for path in (lock_path, features_path))
    check(len(identities) == lock["total_scripts"] == features["total_sources"] == 68
          and identities == lock["blobs"] == features["source_gitblobs"]
          and lock["rc_active_safe_lobby"]["routes"][GAME]["after"] == identities[GAME],
          "CURRENT_ACTIVE")
    check(identities[HORDE] == required["horde"], "ACTUAL_HORDE_DAMAGE_PIN")
    horde = original[HORDE].decode().split("function Horde:hit(", 1)[1].split("function Horde:tick(", 1)[0]
    for marker in ("if m.hp>0 and touched<6 then", "local dealt=math.max(1,math.min(math.floor(damage),40))",
                   "m.hp=math.max(0,beforeHp-dealt)", "local realDamage=beforeHp-m.hp", "return touched,defeated"):
        check(marker in horde, "POSITIVE_HP_DELTA_TOUCHED")
    raw = (PACKAGE / "cue.json").read_bytes()
    check(hashlib.sha256(raw).hexdigest() == required["patch_sha256"], "PATCH_IDENTITY")
    edits = json.loads(raw)
    routes = required["routes"]
    check(set(edits) == set(routes) == {GAME, HUD}, "GAME_AND_HUD_ONLY")
    after = {}
    for name, identity in routes.items():
        check(identities[name] == identity["before"], "INPUT:" + name)
        body = patch(original[name].decode(), edits[name]).encode()
        check(gitblob(body) == identity["after"], "OUTPUT:" + name)
        after[name] = body
    game = after[GAME]
    check(game.count(b"remote.OnServerEvent:Connect(") == 1
          and game.count(b'remote:FireClient(player,{kind="P0D_ATTACK_RESULT"') == 1
          and after[HUD].count(b'attack.Activated:Connect(function() action("ATTACK", nil) end)') == 1,
          "EXISTING_REMOTE_AND_INPUT")
    for name, body in after.items():
        (dist / "src" / name).write_bytes(body)
    check(sources(dist) == original | after, "ONLY_TWO_EXISTING_SOURCES")
    result = identities | {name: routes[name]["after"] for name in after}
    receipt = {"feature": FEATURE, "routes": routes, "horde": required["horde"],
               "origins": required["source_origins"], "studio": "NOT_TESTED_ON_CURRENT_SHA"}
    lock.update(blobs=result, rc_active_confirmed_hit=receipt)
    features.update(source_gitblobs=result, rc_active_confirmed_hit=receipt)
    write_json(lock_path, lock)
    write_json(features_path, features)
    print("ACTIVE_RICH51_FB019_EXACT_GAME_AND_HUD_PASS")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=("rich51", "rich47", "legacy21"))
    parser.add_argument("--off-place", type=Path)
    args = parser.parse_args()
    lock = json.loads((PACKAGE / "source_lock.json").read_bytes())
    if args.profile == lock["profile"] and lock["enabled"] is True:
        if args.off_place is None:
            parser.error("--off-place is required to prove the exact rollback")
        data = args.off_place.read_bytes()
        measured = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        check(measured == lock["off_place"], "OFF_PLACE_MISMATCH")
        print("ACTIVE_RICH51_FB019_OFF_EXACT", json.dumps(measured))
    apply(args.dist,args.profile)
