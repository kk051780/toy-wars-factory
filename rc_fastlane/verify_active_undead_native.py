"""Run selected Game, authored squad and actual Horde HP paths in Native Luau."""

import argparse
from pathlib import Path

from apply_active_undead_squad import GAME, HORDE, PACKAGE, ROLE_RULES, SQUAD, require


def section(source, beginning, end):
    first = source.index(beginning)
    return source[first:source.index(end, first)]


def render(dist, game, baseline, unaimed_control):
    src = dist / "src"
    horde = (src / HORDE).read_text(encoding="utf-8")
    retained_skill = section(game, "local function sevenJobStrike(", "local function applyModeVote(")
    if not baseline:
        require(game.count("SevenJobs.Undead.clear(") == 7, "ALL_LIFECYCLE_CLEAR_SITES")
        require("SevenJobs.Undead.cast(player,{" in retained_skill, "REAL_SKILL_HANDOFF")
    replacements = {
        "__ACTIVE_COMBAT_RULES__": (src / "server/MusouCombatRules.luau").read_text(encoding="utf-8"),
        "__ACTIVE_REAL_HORDE_HIT__": section(horde, "function Horde:hit(", "function Horde:tick("),
        "__ACTIVE_S1_RULES__": (src / "server/S1Rules.luau").read_text(encoding="utf-8"),
        "__ACTIVE_SEVEN_JOBS_RULES__": (src / ROLE_RULES).read_text(encoding="utf-8"),
        "__ORIGINAL_UNDEAD_SQUAD__": (
            PACKAGE / "UndeadSquad.luau" if unaimed_control else src / SQUAD
        ).read_text(encoding="utf-8"),
        "__ACTIVE_REAL_GAME_SKILL__": retained_skill,
        "__IS_BASELINE__": str(baseline).lower(),
    }
    template = (PACKAGE / "native.luau").read_text(encoding="utf-8")
    for label, source in replacements.items():
        require(template.count(label) == 1, "FIXTURE_MARKER:" + label)
        template = template.replace(label, source)
    return template


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", required=True, type=Path)
    parser.add_argument("--before-game", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    current = args.dist / "src" / GAME
    for name, game, baseline, original in (("before", args.before_game, True, False),
                                           ("author", current, False, True),
                                           ("after", current, False, False)):
        body = render(args.dist, game.read_text(encoding="utf-8"), baseline, original)
        args.out.with_name(args.out.stem + "-" + name + args.out.suffix).write_bytes(body.encode("utf-8"))
