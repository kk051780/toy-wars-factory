"""Run the exact MAGE-041 route with the existing growth and neutral scene."""
import argparse
from pathlib import Path

from apply_active_mage_water import PACKAGE, WATER
from verify_active_role_growth_native import make as growth_scene


def make(dist):
    base = growth_scene(dist).decode("utf-8")
    marker = "local function sample(state,now,p)"
    assert base.count(marker) == 1
    base = base.split(marker, 1)[0]
    base = base.replace("local Color3=", "local UDim2={fromOffset=function() return {} end,"
                        "fromScale=function() return {} end}\nlocal Color3=", 1)
    base = base.replace("local growthFlag=true\n", "local growthFlag=true\nlocal waterFlag=true\n", 1)
    base = base.replace('    if attribute=="P0D_RC_ENABLE_MATCH_ROLE_GROWTH" then return growthFlag end\n',
                        '    if attribute=="P0D_RC_ENABLE_MAGE_WATER_BOLT" then return waterFlag end\n'
                        '    if attribute=="P0D_RC_ENABLE_MATCH_ROLE_GROWTH" then return growthFlag end\n', 1)
    catalog = (dist / "src" / WATER).read_text(encoding="utf-8")
    anchor = "local function sevenJobStrike("
    assert base.count(anchor) == 1
    base = base.replace(anchor, "SevenJobs.Water=(function()\n" + catalog + "\nend)()\n" + anchor, 1)
    assert base.count("local picked='WARRIOR'") == 1
    base = base.replace("local picked='WARRIOR'", "local picked='MAGE'", 1)
    return (base + (PACKAGE / "native_cases.luau").read_text(encoding="utf-8")).encode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_bytes(make(args.dist))
