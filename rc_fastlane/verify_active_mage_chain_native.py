"""Exercise the actual MAGE-025 remote, timed Game callbacks, and neutral damage."""
import argparse
from pathlib import Path

from apply_active_mage_chain import CHAIN, GAME, PACKAGE
from verify_active_mage_water_native import make as water_scene
from verify_active_touch_attack_native import emit as touch_scene
from verify_active_undead_native import section


def make(dist):
    existing = water_scene(dist).decode("utf8")
    marker = "local function neutral(id,x,z,hp)"
    assert existing.count(marker) == 1
    base = existing.split(marker, 1)[0]
    src = dist / "src"
    game = (src / GAME).read_text(encoding="utf8")
    module = (src / CHAIN).read_text(encoding="utf8")
    endpoint = section(game, "remote.OnServerEvent:Connect(function(player: Player, data)",
                       "local function onJoin").strip()
    assert endpoint.endswith("end)")
    endpoint = endpoint.replace("remote.OnServerEvent:Connect(function", "local function fireServer", 1)[:-1]
    replacements = {
        "local Horde={}": "local MageChain=(function()\n" + module + "\nend)()\nlocal Horde={}",
        "local function sevenJobStrike(": "SevenJobs.Chain=MageChain\nlocal function sevenJobStrike(",
        "local waterFlag=true\n": "local waterFlag=true\nlocal chainFlag=true\n",
        '    if attribute=="P0D_RC_ENABLE_MAGE_WATER_BOLT" then return waterFlag end':
            '    if attribute=="P0D_RC_ENABLE_MAGE_CHAIN" then return chainFlag end\n'
            '    if attribute=="P0D_RC_ENABLE_MAGE_WATER_BOLT" then return waterFlag end',
        "local CFrame={": "local ColorSequence={new=function(...) return {...} end}\n"
                         "local NumberSequence={new=function(...) return {...} end}\nlocal CFrame={",
        '    if name=="Players" then return Players end':
            '    if name=="Debris" then return {AddItem=function(_,part,seconds)\n'
            '        task.delay(seconds,function() part:Destroy() end)\n'
            '    end} end\n    if name=="Players" then return Players end',
        "local wallX=nil\n": "local wallX=nil\nlocal wallZ=nil\nlocal blockedCasterOnly=false\n",
        "    if blocked or wallX and (from.X<wallX)~=(to.X<wallX) then":
            "    local crossesZ=wallZ and (from.Z<wallZ)~=(to.Z<wallZ)\n"
            "    if blocked or crossesZ or (blockedCasterOnly and from.X<1 and to.Z>.5)\n"
            "        or wallX and (from.X<wallX)~=(to.X<wallX) then",
    }
    for anchor, updated in replacements.items():
        assert base.count(anchor) == 1, anchor
        base = base.replace(anchor, updated, 1)
    return (base + "\n" + endpoint + "\n" + (PACKAGE / "native_cases.luau").read_text(
        encoding="utf8")).encode("utf8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--touch-out", type=Path, required=True)
    options = parser.parse_args()
    options.out.write_bytes(make(options.dist))
    options.touch_out.write_bytes((touch_scene(options.dist) + (PACKAGE / "native_touch.luau").read_text(
        encoding="utf8")).encode("utf8"))
