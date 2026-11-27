"""Mount the three original #382 per-player impact statements in ACTIVE."""
import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources

PACKAGE = Path(__file__).resolve().parent / "features/active_crowd_cap"
FEATURE = "GQ470_FB008_ACTIVE_MINION_PER_PLAYER_CAP_V1"
HORDE = "server/MusouHorde.luau"
ORIGIN = Path(__file__).with_name("apply_fb008_density.py")
REPLACEMENTS = (
    ("    local impacts={}\n    for _,m in ipairs(self.mobs) do",
     "    local impacts={}\n    local impactsByPlayer={}\n    for _,m in ipairs(self.mobs) do"),
    ("            elseif not m.elite and nearest and now>=m.attackAt\n"
     "                and canStrike(nearest,false) then",
     "            elseif not m.elite and nearest and now>=m.attackAt\n"
     "                and (impactsByPlayer[nearest] or 0)<2\n"
     "                and canStrike(nearest,false) then"),
    ('                table.insert(impacts,{player=nearest,damage=3,kind="MINION"})\n'
     '                m.attackAt=now+2.5',
     '                table.insert(impacts,{player=nearest,damage=3,kind="MINION"})\n'
     '                impactsByPlayer[nearest]=(impactsByPlayer[nearest] or 0)+1\n'
     '                m.attackAt=now+2.5'),
)


def replace(raw, edits):
    return patch(raw.decode("utf8"), [
        {"anchor": old, "replace": new} for old, new in edits
    ]).encode("utf8")


def load_pins():
    return json.loads((PACKAGE / "source_lock.json").read_bytes())


def apply(dist, profile, off_place):
    pins = load_pins()
    assert pins["profile"] == "rich51" and pins["feature"] == FEATURE
    assert type(pins["enabled"]) is bool
    if profile != pins["profile"] or not pins["enabled"]:
        return False
    off = off_place.read_bytes()
    assert pins["off_place"] == {"bytes": len(off), "sha256": hashlib.sha256(off).hexdigest()}
    assert gitblob(ORIGIN.read_bytes()) == pins["source_origin"]["adapter_blob"]
    prior = sources(dist)
    hashes = {route: gitblob(raw) for route, raw in prior.items()}
    lock = json.loads((dist / "SOURCE_LOCK.json").read_bytes())
    receipt = json.loads((dist / "RC_FEATURE_LOCK.json").read_bytes())
    assert len(hashes) == 74 and hashes == lock["blobs"] == receipt["source_gitblobs"]
    assert lock["rc_active_ninja_blink"] == receipt["rc_active_ninja_blink"]
    assert lock["rc_active_mage_water"] == receipt["rc_active_mage_water"]
    route = pins["routes"][HORDE]
    assert hashes[HORDE] == route["before"] == lock["rc_active_mage_water"]["routes"][HORDE]["after"]
    updated = replace(prior[HORDE], REPLACEMENTS)
    assert gitblob(updated) == route["after"]
    inverse = [(new, old) for old, new in reversed(REPLACEMENTS)]
    assert replace(updated, inverse) == prior[HORDE]
    (dist / "src" / HORDE).write_bytes(updated)
    assert sources(dist) == prior | {HORDE: updated}
    current = hashes | {HORDE: route["after"]}
    entry = {"feature": FEATURE, "profile": profile, "routes": pins["routes"],
             "source_origin": pins["source_origin"], "off_place": pins["off_place"],
             "ordinary_per_player_per_tick": 2, "elite_excluded_from_cap": True,
             "engine": "NOT_TESTED"}
    lock.update(blobs=current, rc_active_crowd_cap=entry)
    receipt.update(source_gitblobs=current, rc_active_crowd_cap=entry)
    write_json(dist / "SOURCE_LOCK.json", lock)
    write_json(dist / "RC_FEATURE_LOCK.json", receipt)
    print("ACTIVE_CROWD_CAP_IMMEDIATE_OFF_EXACT")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    parser.add_argument("--off-place", type=Path, required=True)
    args = parser.parse_args()
    apply(args.dist, args.profile, args.off_place)
