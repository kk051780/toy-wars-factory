#!/usr/bin/env python3
"""Pinned original V3 author source -> design trace negative-evidence gate.

Source archaeology, NOT Studio simulation, playability proof, or an alternate Game.
Runs only on source-exact #482 snippets; explicit conditions fail if author changes
so a human can re-evaluate gaps rather than silently carry stale "stub" claims.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from check_trace import MATRIX, TraceFailure, git_blob_sha, require

PINS = {
    "EGGRUMBLE_SevenRoleCombat.luau": "66e666418b7c23d41f87faa5d61eb6e2770a463e",
    "EGGRUMBLE_LobbyCastleModesPreview.server.luau": "7162b209bf67b74a71553217f3f744e072a0365d",
    "EGGRUMBLE_CastleMatchRules.luau": "27da5ca1e9e6d9a7afe0674030e387f094ee7492",
    "EGGRUMBLE_FieldItemPickups.luau": "24a35a2e6004c635456cc6f2288cf13f8365ba27",
    "EGGRUMBLE_SwarmCombat.luau": "fea147ac51411e626b410d172aad5cd72615bd45",
}
GAPS = {
    "P0D-008": "PARTIAL",
    "P0D-010": "PARTIAL",
    "P0D-011": "STUB",
    "P0D-012": "STUB",
    "P0D-013": "STUB",
    "P0D-014": "STUB",
    "P0D-015": "STUB",
    "P0D-019": "ABSENT",
}


def require_all(src: str, needles: tuple[str, ...], desc: str) -> None:
    for needle in needles:
        require(needle in src, f"{desc}: expected source expression absent: {needle}")


def role_block(combat: str, role: str) -> str:
    marker = ' elseif role=="' + role + '" then'
    require(combat.count(marker) == 1, f"{role}: role branch is not unique")
    block = combat.split(marker, 1)[1]
    end = block.find('\n elseif role=="')
    if end == -1:
        end = block.find('\n end\nend\nfunction HeroCombat.roleOrder')
    require(end > 0, f"{role}: role branch ending cannot be determined")
    return block[:end]


def run_probe(source: dict[str, str], matrix: dict) -> dict:
    require(set(source) == set(PINS), "expected exactly five original modules")
    combat = source["EGGRUMBLE_SevenRoleCombat.luau"]
    host = source["EGGRUMBLE_LobbyCastleModesPreview.server.luau"]
    rules = source["EGGRUMBLE_CastleMatchRules.luau"]
    item = source["EGGRUMBLE_FieldItemPickups.luau"]
    swarm = source["EGGRUMBLE_SwarmCombat.luau"]
    rows = {r["CONCEPT_ID"]: r for r in matrix["rows"]}
    observations = {}
    for feature, code in GAPS.items():
        require(rows[feature]["GAP_TYPE"] == code, f"{feature}: pinned source and trace diverged")

    # Source-level presence, not engine verification: one original module per authority.
    structural = {
        "CHARACTER": (combat, ('local ORDER={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}', 'function HeroCombat.equip(')),
        "FIELD": (host, ('"TacticalRoute_"', 'for j=1,3 do', '"TacticalBattlefield"')),
        "BATTLE": (combat, ('local function execute(session:any', ':TakeDamage(', 'local function secondaryEffect(')),
        "CASTLE": (rules, ('function M.damageCastle(', 'function M.takeFieldEgg(', 'function M.depositEggs(')),
        "NEUTRAL": (host, ('SwarmCombat.start(session)', 'NeutralStoneGiant.spawn(')),
        "ITEM": (item, ('HEAL={', 'DASH={', 'SHIELD={', 'function Items.start(')),
        "LOBBY": (host, ('local function joinQueue(', 'local function startSession(', 'MODE_SEATS=16')),
        "BALANCE": (rules, ('M.CASTLE_HP=1000', 'M.EGGS_PER_CASTLE=3', 'M.MAX_HERO_SLOTS=16')),
    }
    for domain, (text, needles) in structural.items():
        require_all(text, needles, domain)
        require(any(r["DOMAIN"] == domain for r in matrix["rows"]), f"{domain}: trace coverage missing")
        observations[domain] = "SOURCE_ANCHORS_PRESENT_NOT_ENGINE_PROOF"

    # Current upstream source-specific *negative* evidence for the required 7 jobs.
    heal = combat.split("local function healAllies(", 1)
    require(len(heal) == 2, "Mage heal function missing")
    heal_body = heal[1].split("-- Status effects are real server damage", 1)[0]
    require_all(heal_body, ('characterOf(other)', 'h.Health=math.min(h.MaxHealth,h.Health+25)'), "MAGE_HEAL_ONLY")
    require('LoadCharacter(' not in heal_body and 'Revive' not in heal_body, "MAGE: resurrection source changed; re-audit")
    mage = role_block(combat, "MAGE")
    require_all(mage, ('healAllies(session,p,root);blast()', 'if slot=="A" then blast()'), "MAGE_SLOTS")
    observations["P0D-010"] = "HEAL_ALIVE_ONLY_NO_REVIVE_PROVEN_IN_AUTHOR_MODULE"
    observations["P0D-019"] = "NO_DOWNED_REVIVE_IN_SEVEN_ROLE_MODULE"
    ninja = role_block(combat, "NINJA")
    require_all(ninja, ('EGGRUMBLE_StealthUntil', 'safeMove(char,root,25)'), "NINJA_STEALTH")
    require('Transparency=' not in ninja, "NINJA: visibility code changed; re-audit")
    observations["P0D-011"] = "STEALTH_ATTR_WITHOUT_RENDER_PROOF_IN_THIS_MODULE"
    trapper = role_block(combat, "TRAPPER")
    require_all(trapper, ('if slot=="A" then blast()', 'elseif slot=="B" then', 'safeMove(char,root,20)'), "TRAPPER_ONLY_BLAST")
    require('Instance.new(' not in trapper, "TRAPPER: build/spawn code changed; re-audit")
    observations["P0D-012"] = "NO_DEPLOYABLE_TRAP_IN_THIS_ROLE_BRANCH"
    builder = role_block(combat, "BUILDER")
    require_all(builder, ('"MadScientistTurret"', 'makeEffect(session.world', 'blast()'), "BUILDER_TURRET_VFX")
    require('Instance.new(' not in builder, "BUILDER: construction code changed; re-audit")
    observations["P0D-013"] = "VFX_ONLY_IN_ORIGINAL_BRANCH; #522 ISOLATED SOURCE_EXISTS"
    beast = role_block(combat, "BEAST")
    require_all(beast, ('"BeastFeedGiant"', '"BeastFeedSplit_"', 'makeEffect(session.world'), "BEAST_EFFECTS")
    require('Instance.new(' not in beast, "BEAST: persistent actor code changed; re-audit")
    observations["P0D-014"] = "SHORT_LIVED_VFX_NOT_ACTOR_FOLLOW_GUARD_MOUNT"
    zombie = role_block(combat, "ZOMBIE")
    require_all(zombie, ('"CurseUndead_"', 'makeEffect(session.world', 'blast('), "ZOMBIE_EFFECTS")
    require('Instance.new(' not in zombie, "ZOMBIE: actor generation code changed; re-audit")
    observations["P0D-015"] = "SHORT_LIVED_VFX_NO_COMMANDABLE_AI"
    observations["P0D-008"] = "SEVEN_TOOLS_PRESENT_BUT_CORE_ROLE_ABILITIES_REMAIN_UNVERIFIED_OR_STUBBED"
    # Block assumption that label changes imply role IDs may be mutated.
    require_all(combat, ('NINJA={name="暗殺者"', 'TRAPPER={name="超能力者"', 'ZOMBIE={name="呪術師"'), "EXTERNAL_ROLE_NAMES")
    require(matrix.get("verified_v3_new_official_adopted") == 0, "source-only probe cannot certify official adoption")
    require(matrix.get("verified_v3_owner_accepted") == 0, "source-only probe cannot certify owner acceptance")
    return observations


def fetch_pinned_source(source_dir: Path) -> dict[str, str]:
    result = {}
    for name, expected_blob in PINS.items():
        path = source_dir / name
        raw = path.read_bytes()
        actual = git_blob_sha(raw)
        require(actual == expected_blob, f"{name}: expected original author Git blob {expected_blob}, got {actual}")
        result[name] = raw.decode("utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, default=MATRIX)
    args = parser.parse_args()
    observations = run_probe(fetch_pinned_source(args.source_dir), json.loads(args.matrix.read_text(encoding="utf-8")))
    print(json.dumps({"source_pin": "482:fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
                      "source_level_domains": 8, "actual_engine_qa": "NOT_TESTED",
                      "negative_gaps": {k: observations[k] for k in GAPS},
                      "no_rc_adoption_claim": True}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
