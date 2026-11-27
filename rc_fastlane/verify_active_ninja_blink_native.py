"""Exercise the selected Ninja Q and its exact movement checks in native Luau."""
import argparse
from pathlib import Path

from apply_active_ninja_blink import BLINK, PACKAGE
from verify_active_role_growth_native import make as growth_scene


def make(dist):
    base = growth_scene(dist).decode("utf-8")
    marker = "local function sample(state,now,p)"
    assert base.count(marker) == 1
    base = base.split(marker, 1)[0]
    runtime = (dist / "src" / BLINK).read_text(encoding="utf-8")
    anchor = "local function sevenJobStrike("
    edits = {
        anchor: "SevenJobs.Blink=(function()\n" + runtime + "\nend)()\n" + anchor,
        "local picked='WARRIOR'": "local picked='NINJA'",
        "local growthFlag=true\n": "local growthFlag=true\nlocal blinkFlag=true\n",
        '    if attribute=="P0D_RC_ENABLE_MATCH_ROLE_GROWTH" then return growthFlag end':
            '    if attribute=="P0D_RC_ENABLE_NINJA_BLINK" then return blinkFlag end\n'
            '    if attribute=="P0D_RC_ENABLE_MATCH_ROLE_GROWTH" then return growthFlag end',
        "local function healthy(p) return p.alive,p.root end":
            "local function healthy(p) return p.alive,p.root,p.hum end",
        'Material={SmoothPlastic="SmoothPlastic"}':
            'Material={SmoothPlastic="SmoothPlastic",Air="Air",Water="Water"}',
        "local CFrame={": """Vector3.zero=Vector3.new(0,0,0)
local OverlapParams={new=function() return {} end}
local frameMT={}
function frameMT.__add(frame,step)
    return setmetatable({Position=frame.Position+step,LookVector=frame.LookVector},frameMT)
end
local CFrame={""",
    }
    for old, new in edits.items():
        assert base.count(old) == 1, old
        base = base.replace(old, new, 1)
    return (base + (PACKAGE / "native_cases.luau").read_text(encoding="utf-8")).encode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_bytes(make(args.dist))
