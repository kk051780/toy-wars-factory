"""Run the actual staged wind authority and button layout in Native Luau."""

import argparse
from pathlib import Path

from apply_active_assassin_wind import GAME, HUD, PACKAGE, RULES, require
from verify_active_undead_native import section


def render(dist, game, hud, baseline):
    src = dist / "src"
    edits = {
        "__ACTIVE_CONFIG__": (src / "shared/Config.luau").read_text(encoding="utf-8"),
        "__ACTIVE_S1_RULES__": (src / "server/S1Rules.luau").read_text(encoding="utf-8"),
        "__ACTIVE_WIND_RULES__": (src / RULES).read_text(encoding="utf-8"),
        "__ACTIVE_STOP_WIND__": section(game, "local function stopWind(", "-- Guardian traps stay"),
        "__ACTIVE_APPLY_WIND__": section(game, "local function applyWind(", "local function applyRole("),
        "__ACTIVE_WIND_CLEANUP__": section(game, "    -- Clean up boosts through", '    if match.phase == "LOBBY" then'),
        "__ACTIVE_WIND_HUD__": section(hud, '    trapButton.Visible = s.phase', "end)"),
        "__IS_BASELINE__": str(baseline).lower(),
    }
    template = (PACKAGE / "native.luau").read_text(encoding="utf-8")
    for label, source in edits.items():
        require(template.count(label) == 1, "TEST_MARKER:" + label)
        template = template.replace(label, source)
    return template


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dist", required=True, type=Path)
    p.add_argument("--before-game", required=True, type=Path)
    p.add_argument("--before-hud", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    for name, game, hud, baseline in (
        ("before", args.before_game, args.before_hud, True),
        ("after", args.dist / "src" / GAME, args.dist / "src" / HUD, False),
    ):
        body = render(args.dist, game.read_text(encoding="utf-8"), hud.read_text(encoding="utf-8"), baseline)
        args.out.with_name(args.out.stem + "-" + name + args.out.suffix).write_bytes(body.encode("utf-8"))
