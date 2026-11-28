"""Private common navigation regression on the exact combined and physical OFF Places."""

import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "navigation_entry_sky"
FOLLOWUP = "navigation_entry_sky_followup"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
MAP_POLICY = "ServerScriptService/EGGRUMBLE_MapVisibilityPolicy.luau"
MAP_BRIDGE = "ServerScriptService/EGGRUMBLE_MapIntelBridge.server.luau"
HUD = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime.client.luau"
OTHER_STAGE_ROUTES = {
    "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD.client.luau",
    "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau",
}
PAYLOAD_PINS = {
    "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.server.luau": (
        "7ca85ec2ee9460813f144007527af640c691468cc4957069808f1eececa332d8",
        "bdc8b4f139f482f77dbeb5be18f38448ebefa998fce44c98c449b3c2f135c6c1",
    ),
    MAP_BRIDGE: (
        "603e7bb03bc6d17839afcee4722d847d22b3c9b04381464992de427d0703c00e",
        "e304ad63b157b9d8434ae37aadd56597ed5fe169d752ace81241619a400a4a49",
    ),
    "ServerScriptService/EGGRUMBLE_SevenRoleCombat.luau": (
        "d890a8a0f3ca5b04528115b67b52d61748bfda4197cdfda893eb42564d5388e6",
        "81c1f2aa96e8675d1f6a8df12359c926fe3a19c90590572b16d23540c9ad2907",
    ),
    "ServerScriptService/EGGRUMBLE_SwarmCombat.luau": (
        "18f777b851f259edf9c9cb9b74b7617439ccc2b439da8c8ef38bb31f5fe5837b",
        "40a54e7fc0159641fe4e1b636a48f1b675271a8fa581dcd9e9916a6c886abed3",
    ),
    HUD: (
        "cfafe0a1ba5f014aabb70dbc7775b2b6f2436b0ee6761ae652b84da3d14d2a14",
        "3def22198e468ee9fe86b5bcab46d18fc2fcfa484baea9b75d5fb75c6e91eeeb",
    ),
}
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}
CASE_PINS = {
    "navigation_cases.luau": "d80453b909be1f6fbc76c90c8cd77bcc6dcc0c0eddf6f6d3a2c2a5f2480963fe",
    "return_convert/trapper_return_cases.luau": "a1080361b918bd8c939d6a21b5ebfd1374244fb5aaa3afe8aa8d3d820faa6cf9",
    "ninja_steps_objectives/round_case.luau": "d3072a5d33c5cbcdfe81cca4f11517ae6e2a23eb0bbcc29ce084ea427d877c47",
}
EXPECTED = {
    "guide_home": "real selected Tool A-style item to current own deposit direction at 12 studs, 2 seconds, "
                 "E20/CD14; peer and ordinary map unchanged",
    "guide_return": "real owner-only prior sample is public to actor alone, no movement or HP rollback, "
                    "second utility may coexist; late wall clears",
    "guide_return_denied": "bounds, physical obstruction, an untraversed step, air and carrying fail shut without new disclosures",
    "guide_live_off": "existing live flag retires owners' utility state without touching the selected Footing equipment",
    "guide_stage_four": "authentic S4 samples, 28-stud own direction, 20-stud proven walkback under 24, six-second duration",
    "guide_hud": "actual HUD projects at most two labels and a localized direction row, distinct original cues, "
                 "suppresses foreign and expired payload",
    "guide_physical_off": "exact old 69-source profile retains original map recipient, original Footing, no utility guides",
    "return_player_only": "actual C warns, translates only the same live body and preserves combat and clock state",
    "private_round_custody": "actual PRIVATE selection→TEAM READY with AI roster→enemy egg→human deposit/score"
                             "→results/lobby→voluntary replay",
}
OFF_CASES = {"guide_physical_off"}
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


first90 = _module(HERE / "first90_cues.py", "union22_navigation_first90")
sky = _module(HERE / "sky.py", "union22_navigation_sky")
PROCESS_COUNT = len(EXPECTED) + first90.PROCESS_COUNT + sky.PROCESS_COUNT
FILES |= first90.FILES | sky.FILES


def _extra_runs(binary):
    for mode,case in first90.CASES.items():
        yield case,[binary.name,f"{OUTPUT_NAME}/{case}.luau"],mode
    for case,mode in sky.CASES.items():
        yield case,[binary.name,f"{OUTPUT_NAME}/{sky.PROGRAMS[mode]}","-a",case],None


def _assert_extra(case,mode,stdout,stderr,status):
    if mode is None:
        return [sky.assert_result(case,stdout,stderr,status)]
    return list(first90.assert_result(mode,stdout,stderr,status))


def _once(source, boundary, replacement, compose):
    compose.need(source.count(boundary) == 1, "NAVIGATION_ENTRY_SKY_BOUNDARY:" + boundary)
    return source.replace(boundary, replacement, 1)


def _profile_pins(profile, compose):
    stages = tuple(compose.RECENT_TRIAL_STAGES)
    compose.need(stages.count(FOLLOWUP) == 1, "NAVIGATION_ENTRY_SKY_STAGE")
    current = profile["sources"]
    index = stages.index(FOLLOWUP)
    after = (compose.trial_sources_before(profile, stages[index - 1]) if index else
             {name: row["after"] for name, row in current.items()})
    before = compose.trial_sources_before(profile, FOLLOWUP)
    rows = profile[FOLLOWUP]["rows"]
    scope = set(PAYLOAD_PINS) | OTHER_STAGE_ROUTES
    compose.need(set(after) == set(before) == set(current) and len(after) == 69
                 and set(rows) == scope
                 and {name for name in after if after[name] != before[name]} == scope,
                 "NAVIGATION_ENTRY_SKY_SCOPE")
    compose.need(all(row["parent"]["before"] == current[name]["before"]
                     and row["parent"]["after"] == before[name] for name, row in rows.items()),
                 "NAVIGATION_ENTRY_SKY_PROFILE_ROWS")
    for route, pinned in PAYLOAD_PINS.items():
        compose.need((after[route]["sha256"], before[route]["sha256"]) == pinned,
                     "NAVIGATION_ENTRY_SKY_COMPOUND_SOURCE:" + route)
    return {ON_PROGRAM: after, OFF_PROGRAM: before}


def _fixture_inputs(native, compose):
    manifest = compose.read_file(native / "mage_projectiles" / "INPUTS.json")
    engine = compose.read_file(native / "mage_projectiles" / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(engine)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "NAVIGATION_ENTRY_SKY_MANIFEST")
    upstream = compose.strict_json(manifest)
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "NAVIGATION_ENTRY_SKY_ENGINE")
    helpers = {}
    for name, expected in TEMPLATE_PINS.items():
        module = _module(native / name / "__init__.py", "union22_navigation_entry_sky_" + name)
        source = inspect.getsource(module._template).replace("\r\n", "\n").encode("utf-8")
        fixtures[name + "_template"] = compose.identity(source)
        compose.need(fixtures[name + "_template"]["sha256"] == expected,
                     "NAVIGATION_ENTRY_SKY_TEMPLATE_PIN:" + name)
        helpers[name] = module
    template = helpers["footing_wards"]._template(engine, helpers, compose)
    # A real Roblox Humanoid's initial Sit/PlatformStand values are both false.
    template = _once(template, "FloorMaterial=Enum.Material.Concrete,",
                     "FloorMaterial=Enum.Material.Concrete,Sit=false,PlatformStand=false,", compose)
    fixtures["rendered_template"] = compose.identity(template.encode("utf-8"))
    compose.need(fixtures["rendered_template"]["sha256"]
                 == "c7fffca5e4313573be4575b38e8120e395b7ebfdc57c6ee8115e639fd41cc1bc",
                 "NAVIGATION_ENTRY_SKY_EFFECTIVE_TEMPLATE")
    common = _module(native / "mage_water_chain" / "__init__.py", "union22_navigation_entry_sky_shared_cases")
    shared_cases = compose.read_file(native / "mage_water_chain" / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA,
                 "NAVIGATION_ENTRY_SKY_SHARED_CASES")
    cases = []
    for name, expected in CASE_PINS.items():
        raw = compose.read_file((native if "/" in name else HERE) / name)
        fixtures[name] = compose.identity(raw)
        compose.need(fixtures[name]["sha256"] == expected, "NAVIGATION_ENTRY_SKY_CASE_PIN:" + name)
        cases.append(raw.decode("utf-8"))
    return common, upstream["runtime_routes"], template, shared_cases.decode("utf-8"), cases, fixtures


def _program(common, sources, routes, template, base, cases, on, compose):
    body = _once(cases[0], "-- MAP_POLICY_SOURCE", sources[MAP_POLICY], compose)
    body = _once(body, "-- MAP_BRIDGE_SOURCE", sources[MAP_BRIDGE], compose)
    hud = sources[HUD]
    first = "-- COMMON-011/020. One private line"
    last = "-- End COMMON route presentation."
    view = "local CommonGuideView=nil"
    if on:
        compose.need(hud.count(first) == hud.count(last) == 1 and hud.index(first) < hud.index(last),
                     "NAVIGATION_ENTRY_SKY_HUD_SOURCE_BOUNDARY")
        view = hud[hud.index(first):hud.index(last)]
    else:
        compose.need(first not in hud, "NAVIGATION_ENTRY_SKY_PHYSICAL_OFF_HUD")
    body = _once(body, "-- GUIDE_HUD_SOURCE", view, compose)
    return common._program(sources, routes, template, "\n".join((base, body, *cases[1:])), compose)


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    common, routes, template, base, cases, fixtures = _fixture_inputs(native, compose)
    pins = _profile_pins(profile, compose)
    historical = tuple(compose.RECENT_TRIAL_STAGES).index(FOLLOWUP) > 0
    on_root = source_root.parent / compose.MOBILITY_CRESTS_OFF / "sources" if historical else source_root
    off_root = source_root.parent / compose.NAVIGATION_ENTRY_SKY_OFF / "sources"
    generated = {}
    for filename, root in ((ON_PROGRAM, on_root), (OFF_PROGRAM, off_root)):
        bodies = common._sources(root, pins[filename], compose)
        generated[filename] = _program(common, bodies, routes, template, base, cases, filename == ON_PROGRAM, compose)
    for mode,root,pin in (("ON",on_root,pins[ON_PROGRAM]),("OFF",off_root,pins[OFF_PROGRAM])):
        generated[first90.CASES[mode]+".luau"] = first90.program(root,mode)
        generated[sky.PROGRAMS[mode]] = sky.program(root,mode,compose,pin)
    fixtures["first90_context"] = first90.FIXTURE_PINS
    fixtures["sky959_cases"] = compose.identity(compose.read_file(HERE / "sky_cases.luau"))
    return generated, pins, fixtures


def _args(case, binary):
    filename = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{filename}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "NAVIGATION_ENTRY_SKY_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, program in generated.items():
        compose.need(compose.read_file(output / name) == program, "NAVIGATION_ENTRY_SKY_GENERATED:" + name)
    cases = {}
    for case, text in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{text}"
        expected = (marker + "\n").encode("utf-8")
        compose.need(status == b"0\n" and stderr == b""
                     and stdout in (expected, expected.replace(b"\n", b"\r\n")),
                     "NAVIGATION_ENTRY_SKY_RESULT:" + case)
        cases[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                       "stderr": compose.identity(stderr), "status": compose.identity(status)}
    for case,args,mode in _extra_runs(binary):
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        compose.need(status == b"0\n", "NAVIGATION_ENTRY_SKY_EXTRA_STATUS:" + case)
        markers = _assert_extra(case,mode,stdout,stderr,0)
        cases[case] = {"argv":args,"markers":markers,"stdout":compose.identity(stdout),
                       "stderr":compose.identity(stderr),"status":compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": cases, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()),
                 "NAVIGATION_ENTRY_SKY_FILESET")
    observed = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == observed,
                 "NAVIGATION_ENTRY_SKY_RECEIPT")
    return observed


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "NAVIGATION_ENTRY_SKY_OUTPUT")
    _binary(binary, binary_pin, compose)
    prepared = _prepare(source_root, profile, compose)
    output.mkdir()
    for name, program in prepared[0].items():
        (output / name).write_bytes(program)
    from case_batch import run_cases

    def run_case(case):
        proc = subprocess.run([str(binary.resolve()), *_args(case, binary)[1:]], cwd=output.parent,
                              capture_output=True, env=environment, timeout=60)
        (output / f"{case}.stdout.log").write_bytes(proc.stdout)
        (output / f"{case}.stderr.log").write_bytes(proc.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{proc.returncode}\n".encode("ascii"))
        compose.need(proc.returncode == 0, "NAVIGATION_ENTRY_SKY_EXIT:" + case)
    run_cases(EXPECTED, run_case)
    extras={case:(args,mode) for case,args,mode in _extra_runs(binary)}

    def run_extra(case):
        args,mode=extras[case]
        _binary(binary, binary_pin, compose)
        proc = subprocess.run([str(binary.resolve()),*args[1:]],cwd=output.parent,
                              capture_output=True,env=environment,timeout=110)
        (output / f"{case}.stdout.log").write_bytes(proc.stdout)
        (output / f"{case}.stderr.log").write_bytes(proc.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{proc.returncode}\n".encode("ascii"))
        _assert_extra(case,mode,proc.stdout,proc.stderr,proc.returncode)
    run_cases(extras, run_extra)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
