#!/usr/bin/env python3
"""Read-only cross-author acceptance against the ACTUAL composed #510+#516 Combat.

Executes source-extracted original #482 roster + MAGE heal and #516 delayed
status callbacks in pinned native Luau. Original Game/Remote/RC never changed.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMBINED_SHA256 = "4b7b69664a572f57ed327c4b7cb23ea4209ce8022e4aa86cd2e4110f049b5293"
STATUS_OWNER_SHA = "dfafbd8ca92eff3017a49fb010e696f6afc07455"

def import_patch():
    name = "_own_original_author_mage_patch"
    spec = importlib.util.spec_from_file_location(name, HERE / "build_candidate.py")
    assert spec and spec.loader
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--combat", required=True, type=Path)
    parser.add_argument("--author", required=True, type=Path)
    parser.add_argument("--status", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    m = import_patch()
    author = args.author.resolve(strict=True)
    status = args.status.resolve(strict=True)
    source = args.combat.resolve(strict=True).read_bytes()
    original = (author / "EGGRUMBLE_SevenRoleCombat.luau").read_bytes()
    rules = (author / "EGGRUMBLE_CastleMatchRules.luau").read_bytes()
    actors = (author / "EGGRUMBLE_BotActors.luau").read_bytes()
    assert m.git_blob(original) == m.SOURCE_BLOB
    assert m.git_blob(rules) == m.RULES_BLOB
    assert m.git_blob(actors) == m.ACTORS_BLOB
    # #516 combined Combat is the already proven other-owner immutable output:
    # our updated test harness MUST NOT change or re-compose the actual game.
    assert hashlib.sha256(source).hexdigest() == COMBINED_SHA256, (
        "prior owner-verified Combat changed: require new explicit same-source approval"
    )
    combined = source.decode("utf-8")
    original_text = original.decode("utf-8")
    status_start = "local function secondaryEffect("
    status_end = "\nlocal function execute("
    heal_start = "local function healAllies("
    heal_end = "\n-- Status effects are real server damage / movement changes"
    def section(src, begin, end):
        assert src.count(begin) == 1 and src.count(end) == 1
        return src.split(begin, 1)[1].split(end, 1)[0]
    assert section(combined, heal_start, heal_end) == section(
        m.patch(original_text), heal_start, heal_end
    ), "MAGE source integration diverged"
    assert section(combined, status_start, status_end) != section(
        original_text, status_start, status_end
    ), "status fence absent"
    assert combined.count("StatusTickFence.canTick(") == 1
    assert combined.count("botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)") == 1
    assert "local function healAllies(" in combined and "StatusTickFence.canTick(" in combined
    assert "session.botActors=bots" in actors.decode("utf-8")
    assert 'model:SetAttribute("EGGRUMBLE_BotId",id)' in actors.decode("utf-8")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "original.luau").write_text(
        m.harness(original_text, fixed=False, rules=rules.decode("utf-8")),
        encoding="utf-8",
    )
    (out / "combined.luau").write_text(
        m.harness(combined, fixed=True, rules=rules.decode("utf-8")),
        encoding="utf-8",
    )
    enemy = "teammate.team==state.team"
    assert combined.count(enemy) == 1
    hostile_mutant = combined.replace(enemy, "teammate.team~=state.team", 1)
    (out / "mutant_enemy.luau").write_text(
        m.harness(hostile_mutant, fixed=True, rules=rules.decode("utf-8")),
        encoding="utf-8",
    )
    wall = (
        "and lineClear(root.Position+Vector3.new(0,1.5,0),\n"
        "     botRoot.Position+Vector3.new(0,1,0),sourceCharacter,bot)"
    )
    assert combined.count(wall) == 1, "healing wall fence layout drift"
    wall_mutant = combined.replace(wall, "and true", 1)
    (out / "mutant_wall.luau").write_text(
        m.harness(wall_mutant, fixed=True, rules=rules.decode("utf-8")),
        encoding="utf-8",
    )
    (out / "StatusFence.luau").write_bytes(
        (status / "EGGRUMBLE_StatusTickFence.luau").read_bytes()
    )
    subprocess.run(
        [
            sys.executable,
            str(status / "tools/make_actual_status_callback_native.py"),
            "--source", str(args.combat.resolve(strict=True)),
            "--out", str(out / "status.luau"),
        ],
        check=True,
    )
    receipt = {
        "source_union_sha256": COMBINED_SHA256,
        "source_author_482_combat_git_blob": m.SOURCE_BLOB,
        "source_author_482_rules_git_blob": m.RULES_BLOB,
        "source_author_482_botactors_git_blob": m.ACTORS_BLOB,
        "source_status_516_head": STATUS_OWNER_SHA,
        "source_mage_510": "latest current branch",
        "negative_mutants": ["enemy team-heal inversion", "bot wall-LOS bypass"],
        "original_1human_15bot_roster_executed": "pending Native run",
        "status_delayed_callback_executed": "pending Native run",
        "status": "PRIVATE_NATIVE_QA_NOT_FORMAL_RC_NOT_STUDIO",
        "official_rc_adopted": False,
        "rollback": "omit all private patches, restore original source per #220 sole authorized writer",
    }
    (out / "RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("GQ_510_516_CROSS_AUTHOR_SOURCE_SELECTIVE_BLOB_LOCK_PASS", COMBINED_SHA256)
    print("MAGE_ORIGINAL_ROSTER_AND_STATUS_TEST_GENERATED", 2, "malicious mutants")

if __name__ == "__main__":
    main()
