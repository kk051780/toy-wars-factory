"""Run actual selected Horde movement and attacks in the native Luau VM."""
import argparse
import re
import subprocess
from pathlib import Path

from apply_active_crowd_cap import HORDE, PACKAGE, REPLACEMENTS, load_pins, replace
from integrate import gitblob

NATIVE_MOCKS = PACKAGE.parent / "active_undead_squad/native.luau"
CAP = "(impactsByPlayer[nearest] or 0)<2"


def selected_scene(dist, body, capped):
    src = dist / "src/server"
    rules = (src / "MusouCombatRules.luau").read_text(encoding="utf8")
    fixture = (PACKAGE / "native_scene.luau").read_text(encoding="utf8")
    start = 'local Combat=require(script.Parent:WaitForChild("MusouCombatRules"))'
    assert body.count(start) == 1, "HORDE_IMPORT_DRIFT"
    horde = body.replace(start, "local Combat=(function()\n" + rules + "\nend)()", 1)
    assert horde.rstrip().endswith("return Horde"), "HORDE_END_DRIFT"
    horde = horde.rsplit("return Horde", 1)[0]
    geometry = (src / "MapBuilder.luau").read_text(encoding="utf8")
    for name in ("GrassArena", "CenterRoad"):
        pattern = rf'part\(folder, "{name}", Vector3.new\(([^)]+)\), Vector3.new\(([^)]+)\), COLOR\.'
        matches = re.findall(pattern, geometry)
        assert len(matches) == 1, f"MAP_FLOOR_DRIFT:{name}"
        size, position = matches[0]
        fixture = fixture.replace(f"__{name}_SIZE__", size).replace(f"__{name}_POS__", position)
    mocks = NATIVE_MOCKS.read_text(encoding="utf8")
    assert mocks.count("local nativeType=typeof") == 1
    ui, scene = fixture.split("-- Native Horde scene", 1)
    return mocks.split("local nativeType=typeof", 1)[0] + ui + horde + scene.replace(
        "__EXPECT_CAP__", str(capped).lower())


def mutants(body):
    text = body.decode("utf8")
    normal = text.replace("                and " + CAP + "\n", "", 1)
    shared = text.replace("impactsByPlayer[nearest]", 'impactsByPlayer["all"]')
    padding = " " * 20
    elite_line = padding + 'table.insert(impacts,{player=target,damage=11,kind="ELITE"})'
    assert text.count(elite_line) == 1, "ELITE_IMPACT_DRIFT"
    elite = text.replace(elite_line, padding + 'if next(impactsByPlayer)==nil then\n'
                         + "    " + elite_line + "\n" + padding + "end", 1)
    sticky = "local impactsByPlayer={}\n" + text.replace("    local impactsByPlayer={}\n", "", 1)
    cases = {
        "missing": (normal, "SOLO_PEAK_T5"),
        "shared": (shared, "DUAL_PLAYER_SEPARATE_LIMITS"),
        "elite": (elite, "ELITE_INDEPENDENT_OF_NORMAL_CAP"),
        "sticky": (sticky, "NEXT_TICK_CAP_RESET"),
    }
    assert all(variant != text for variant, _ in cases.values())
    return cases


def verify(dist, out, luau, before):
    before_raw = before.read_bytes()
    selected_raw = (dist / "src" / HORDE).read_bytes()
    pin = load_pins()["routes"][HORDE]
    assert gitblob(before_raw) == pin["before"] and gitblob(selected_raw) == pin["after"]
    assert replace(before_raw, REPLACEMENTS) == selected_raw
    cases = {"before": (before_raw.decode("utf8"), None),
             "selected": (selected_raw.decode("utf8"), None)} | mutants(selected_raw)
    out.mkdir(parents=True, exist_ok=True)
    for name, (source, failure) in cases.items():
        scene = out / f"active-crowd-{name}.luau"
        scene.write_bytes(selected_scene(dist, source, name != "before").encode("utf8"))
        result = subprocess.run([str(luau), str(scene)], capture_output=True, timeout=20)
        stdout = result.stdout.decode("utf8").replace("\r\n", "\n").strip()
        stderr = result.stderr.decode("utf8").replace("\r\n", "\n").strip()
        if failure is None:
            assert result.returncode == 0 and not stderr, (name, stdout, stderr)
            assert stdout.endswith("ACTIVE_FB008_ACTUAL_SELECTED_HORDE_PASS")
            print(name, stdout)
        else:
            assert result.returncode != 0 and (": " + failure) in stderr, (name, stdout, stderr)
            print(f"ACTIVE_FB008_NEGATIVE_REJECTED {name} {failure}")
    print("ACTIVE_FB008_SOLO_DUAL_ELITE_AND_NEXT_TICK_NATIVE_PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("dist", "out", "luau", "before"):
        parser.add_argument("--" + arg, type=Path, required=True)
    options = parser.parse_args()
    verify(options.dist, options.out, options.luau, options.before)
