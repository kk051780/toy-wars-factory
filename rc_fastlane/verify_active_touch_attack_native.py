"""Compile the current HUD's own layout and feedback paths into a local Native test."""

import argparse
from pathlib import Path

from apply_active_touch_attack import HUD, PACKAGE
from verify_active_undead_native import section


def emit(dist):
    hud = (dist / "src" / HUD).read_text(encoding="utf-8")
    fixture = (PACKAGE / "native_cases.luau").read_text(encoding="utf-8")
    if '"MageChainAbility"' in hud:
        fixture = fixture.replace("__EXACT_TOUCH_LAYOUT__", """
local chainCast={Visible=false,Size=UDim2.fromOffset(94,56),Position=UDim2.fromOffset(252,551)}
__EXACT_TOUCH_LAYOUT__""", 1)
    return fixture.replace("__EXACT_ATTACK_FEEDBACK__", section(
        hud, "local originalAttackText = attack.Text", "trapButton.MouseButton1Click:Connect"
    )).replace("__EXACT_TOUCH_LAYOUT__", section(
        hud, "local function touchAttackPosition(", "remote.OnClientEvent:Connect(function(s)"
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_bytes(emit(args.dist).encode("utf-8"))
