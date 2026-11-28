"""Verify the selected PRIVATE water/lightning Tool, Host, Swarm and HUD paths."""
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "mage_projectiles"
INPUTS_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
CASES_SHA = "9d931c5c8a595749eff580d5814de8fa62bed57cddee33650eb983f94f8630d2"
OUTPUT_NAME = "mage_water_chain"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
HUD = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau"
EXPECTED = {
    "water_a": "Host equip then actual Tool A HP −16/E30, S0 cue 1.0→0.5→absent and 12s CD",
    "lightning_c": "actual C E40 and visible .24s tell; actual solid between tell/impact prevents damage",
    "combo_d": "actual D only one E80, one after-tell hit, one direct water mark consumed",
    "component_a": "actual D separately arms slot A for 12s; sufficient E before and after edge",
    "component_c": "actual D separately arms slot C for 20s; sufficient E before and after edge",
    "component_d": "actual D separately arms slot D for 40s; sufficient E before and after edge",
    "component_guard": "live A lock rejects D atomically with E80 available; C retains its own acceptance and damage",
    "negative_avatar": "actual warned D cancels and cue clears on avatar",
    "negative_exit": "actual warned D cancels and cue clears on exit",
    "negative_egg": "actual warned D cancels and cue clears on egg",
    "negative_off": "actual warned D cancels and cue clears on off",
    "old_standard": "actual no-D standard A/B/C tools, neutral damage and legacy healing preserved",
    "old_projectile": "previous Wind option still uses genuine old flight and unaffected Tool inventory",
    "off": "actual no-D standard A/B/C tools, neutral damage and legacy healing preserved",
    "hud_loadout_transition": "same HUD casts actual D in first Host match, then falls back and casts actual legacy B in the next",
}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _sources(root, pins, compose):
    compose.need(root.is_dir() and not root.is_symlink() and not root.parent.is_symlink(),
                 "MAGE_WATER_CHAIN_SOURCE_DIRECTORY")
    paths = list(root.rglob("*"))
    compose.need(all(not path.is_symlink() and (path.is_file() or path.is_dir()) for path in paths)
                 and len(pins) == 69 and {path.relative_to(root).as_posix() for path in paths if path.is_file()}
                 == set(pins), "MAGE_WATER_CHAIN_SOURCE_FILESET")
    bodies = {}
    for name, pin in pins.items():
        raw = compose.read_file(root / name)
        compose.need(compose.identity(raw) == pin, "MAGE_WATER_CHAIN_SOURCE:" + name)
        bodies[name] = raw.decode("utf-8")
    return bodies


def _program(bodies, routes, fixture, cases, compose):
    hud = bodies[HUD]
    if "CommonGuideView.render(" in hud:
        first = "-- COMMON-011/020. One private line"
        last = "-- End COMMON route presentation."
        fixture_render = " local function render()\n local char=player.Character\n"
        compose.need(hud.count(first) == hud.count(last) == cases.count(fixture_render) == 1
                     and hud.index(first) < hud.index(last), "MAGE_WATER_CHAIN_REAL_GUIDE_SCOPE")
        # The selected render now calls this real earlier local. Give the
        # partial HUD harness the same declaration before its extracted render.
        guide = hud[hud.index(first):hud.index(last)]
        cases = cases.replace(fixture_render, guide + fixture_render, 1)
    cuts = {
        "__HUD_DRAWER__": ('local skillUse=button("SelectedSkillUse"',
                          "-- GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120"),
        "__HUD_SELECTED_USE__": ("skillUse.Activated:Connect(function()",
                                "-- Both buttons activate ONLY original server-owned Tools"),
        "__HUD_SELECTED_RENDER__": (' actions.ATTACK.Text=basicTool() and "攻撃" or "技A"',
                                    " -- Read current server publications in this existing .16s tick"),
    }
    for marker, (start, end) in cuts.items():
        compose.need(cases.count(marker) == hud.count(start) == hud.count(end) == 1
                     and hud.index(start) < hud.index(end), "MAGE_WATER_CHAIN_HUD:" + marker)
        cases = cases.replace(marker, hud[hud.index(start):hud.index(end)])

    lines, declarations, ranges = [], {}, {}
    inserted = False
    for line in fixture.splitlines():
        if line.startswith("-- RANGE:"):
            alias = line.removeprefix("-- RANGE:")
            compose.need(alias in routes and alias not in declarations, "MAGE_WATER_CHAIN_RANGE")
            if alias == "BasicMobilityPolicy":
                # Roblox effects and Tool signal boundaries for the existing Native mock.
                lines.extend(["local ColorSequence={new=function(...) return {...} end}",
                              "local NumberSequence={new=function(...) return {...} end}",
                              "function methods:EquipTool(tool) tool.Parent=self.Parent end",
                              "function methods:Activate() self.Activated:Fire() end"])
            declarations[alias] = len(lines)
            lines.append("")
        elif line.startswith("-- SOURCE:"):
            alias = line.removeprefix("-- SOURCE:")
            compose.need(alias in routes and alias not in ranges, "MAGE_WATER_CHAIN_BODY")
            first = len(lines) + 1
            lines.extend(bodies[routes[alias]].splitlines())
            ranges[alias] = (first, len(lines))
        elif line == "-- MAGE_RUNTIME_CASES":
            compose.need(not inserted, "MAGE_WATER_CHAIN_CASE_INSERTION")
            lines.extend(cases.splitlines())
            inserted = True
        else:
            lines.append(line)
    compose.need(inserted and routes.keys() == ranges.keys() == declarations.keys(),
                 "MAGE_WATER_CHAIN_TEMPLATE_BOUNDARY")
    for alias, (first, last) in ranges.items():
        lines[declarations[alias]] = f"fullSourceRanges.{alias}={{first={first},last={last}}}"
    return ("\n".join(lines) + "\n").encode("utf-8")


def _prepare(source_root, profile, compose):
    inputs = compose.read_file(SHARED / "INPUTS.json")
    fixture = compose.read_file(SHARED / "engine_fixture.luau")
    cases = compose.read_file(HERE / "cases.luau")
    fixture_pins = {"inputs": compose.identity(inputs), "engine": compose.identity(fixture),
                    "cases": compose.identity(cases)}
    compose.need(fixture_pins["inputs"]["sha256"] == INPUTS_SHA
                 and fixture_pins["cases"]["sha256"] == CASES_SHA, "MAGE_WATER_CHAIN_INPUT_PINS")
    shared = compose.strict_json(inputs)
    compose.need(fixture_pins["engine"] == shared["fixtures"]["engine_fixture.luau"],
                 "MAGE_WATER_CHAIN_ENGINE_FIXTURE")
    routes = shared["runtime_routes"]
    after = {name: row["after"] for name, row in profile["sources"].items()}
    changed = profile["mage_water_chain_followup"]["rows"]
    compose.need(set(changed) == {HUD, routes["Host"], routes["SwarmCombat"], routes["SevenRoleCombat"]}
                 and all(row["parent"]["before"] == profile["sources"][name]["before"]
                         and row["parent"]["after"] != after[name] for name, row in changed.items()),
                 "MAGE_WATER_CHAIN_PROFILE_SCOPE")
    before = compose.trial_sources_before(profile, "mage_water_chain_followup")
    off_root = source_root.parent / compose.MAGE_WATER_CHAIN_OFF / "sources"
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    generated = {}
    for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root)):
        generated[name] = _program(_sources(root, pins[name], compose), routes,
                                   fixture.decode("utf-8"), cases.decode("utf-8"), compose)
    return generated, pins, fixture_pins


def _args(case, binary):
    program = OFF_PROGRAM if case == "off" else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{program}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "MAGE_WATER_CHAIN_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "MAGE_WATER_CHAIN_GENERATED:" + name)
    observed = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "MAGE_WATER_CHAIN_RESULT:" + case)
        observed[case] = {"argv": _args(case, binary), "marker": marker,
                          "stdout": compose.identity(stdout), "stderr": compose.identity(stderr),
                          "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": observed, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()),
                 "MAGE_WATER_CHAIN_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result,
                 "MAGE_WATER_CHAIN_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "MAGE_WATER_CHAIN_OUTPUT")
    prepared = _prepare(source_root, profile, compose)
    output.mkdir()
    for name, raw in prepared[0].items():
        (output / name).write_bytes(raw)
    from case_batch import run_cases

    def run_case(case):
        _binary(binary, binary_pin, compose)
        args = [str(binary.resolve()), *_args(case, binary)[1:]]
        result = subprocess.run(args, cwd=output.parent, capture_output=True, env=environment, timeout=110)
        (output / f"{case}.stdout.log").write_bytes(result.stdout)
        (output / f"{case}.stderr.log").write_bytes(result.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{result.returncode}\n".encode("ascii"))
        compose.need(result.returncode == 0, "MAGE_WATER_CHAIN_EXIT:" + case)
    run_cases(EXPECTED, run_case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
