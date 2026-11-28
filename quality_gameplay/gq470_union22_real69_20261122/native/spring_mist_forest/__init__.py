"""Exercise Builder, Zombie, Beast, and the selected FlagshipFieldArt server source."""
import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "spring_mist_forest"
FOLLOWUP = "spring_mist_forest_followup"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
ART_ON_PROGRAM, ART_OFF_PROGRAM = "generated_art_on.luau", "generated_art_off.luau"
FIELD_ART = "ServerScriptService/EGGRUMBLE_FlagshipFieldArt.server.luau"
FIELD_INSERT = "-- INSERT_SELECTED_FIELD_ART"
ART_BUDGET = b"ART_BUDGET\t320\t219\t62\t105"
ART_ROUTES = {"bytes": 2531, "sha256": "142c90627c1ae22db54c1c862a0fa4bdd966c25f516bd757734d1f1e2d1b0845"}
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}
CASE_PINS = {
    "builder_cases.luau": "b10fe03967942a55742ff5d3fcc82c647eaa80615c33a5b3f1fe318eb2eca4f9",
    "beast_cases.luau": "144746ac81e57dcef20d956c07ee3a42a761ee10f37071c6f5117bd6e3d3c64c",
    "zombie_cases.luau": "1733377203eb8ca4190b86706052ffdcfde00ddb4923619867390920643b162a",
    "forest_cases.luau": "cbf56239866bbc3cb43b8ace944540ffce6534ac16464a3a79db9b16e29459fe",
    "builder_forms/zombie_rune_cases.luau": "b6aeb896c23e1fed1c079f5fbc0c2f71c73792ecdcad22f1fef43278363aa600",
    "ninja_beast_castle/beast_cases.luau": "f4a10c4dd3a30463c68fae561e48e2a7d74f9c70dac1f384ec1a9d40827a8df8",
}
EXPECTED = {
    "builder_works_guard": "one guard consumes E40, follows its owner and mitigates the actual neutral contact for three seconds",
    "builder_works_pad": "one owner-authoritative physical launch, with no remote or stored reward",
    "builder_works_blocked": "blocked geometry never produces half of a pair or charges energy",
    "builder_works_ceiling": "vertical sweep prevents clipping a late overhead obstacle",
    "builder_works_combo": "exact guard, placement and verified jump receipts use one E80 and no extra life",
    "builder_works_egg_and_air": "current custody and a safe grounded start are checked at both boundaries",
    "builder_works_live_off": "independent runtime rollback clears devices, contact reduction and optional Tools",
    "builder_works_physical_off": "the actual prior build keeps the original Builder kit",
    "beast_061_ember": "one real existing B fox-tagged effect burns one eligible neutral without direct HP; stone resistance and expiry preserved",
    "beast_062_frost": "actual neutral patrol displacement reduced from 2.28 to 2.052 studs; ice resistance and no HP preserved",
    "beast_067_chain_s0": "real S0 one distinct link uses existing 10 resisted HP and one visible receipt; another creature untouched",
    "beast_067_chain_s1": "live role S1 two legal links from distinct points; shielded closest and excess targets remain unharmed",
    "beast_elements_cancel": "unowned or water-bound escort costs zero; retirement of exact B creature cancels real pending status and HP",
    "beast_elements_live_off": "the original switch cannot revoke element kit; correct OFF clears cue and tool and restores original A/B/C",
    "beast_elements_physical_off": "exact ancestor keeps original single optional deck and existing normal skill selection on second interaction",
    "path087": "087 tells for .5 seconds, moves the same avatar exactly four studs, and changes no other authority",
    "path087_s4": "087 natural S4 moves exactly twelve studs after the same .5 second warning",
    "path087_oldsquad": "087 leaves the original C-created three actual owned servants untouched",
    "path087_castle": "087 does not bypass the actual open castle entrance or write enemy castle HP",
    "path087_deny_latewall": "087 rejects latewall without transfer or late appearance",
    "path087_deny_egg": "087 rejects egg without transfer or late appearance",
    "path087_deny_off": "087 rejects off without transfer or late appearance",
    "path041": "041 actual safe local floor telegraph produces a low one-second harmless visual band",
    "path044": "044 marks one checked floor point six studs away for two seconds and has no movement or HP authority",
    "path_physical_off": "exact old physical game keeps its old Zombie route and has no gate option",
    "forest421_on": "two exact biome palettes and four opaque ancient gate silhouettes replace old pieces on real same Host field",
    "forest421_flag_off": "runtime flag false on arena creation restores the original forest without changing source owners",
    "forest421_physical_off": "byte exact prior FieldArt has original forest, same route marks and baseline scene allocation",
}
ART_CASES = {"forest421_on", "forest421_flag_off", "forest421_physical_off"}
OFF_CASES = {"builder_works_physical_off", "beast_elements_physical_off", "path_physical_off", "forest421_physical_off"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, ART_ON_PROGRAM, ART_OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "SPRING_MIST_FOREST_MANIFEST")
    upstream = compose.strict_json(manifest)
    routes = upstream["runtime_routes"]
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "SPRING_MIST_FOREST_ENGINE")
    helpers = {}
    for label, want in TEMPLATE_PINS.items():
        helper = _module(native / label / "__init__.py", "union22_spring_mist_forest_" + label)
        source = inspect.getsource(helper._template).replace("\r\n", "\n").encode("utf-8")
        fixtures[label + "_template"] = compose.identity(source)
        compose.need(fixtures[label + "_template"]["sha256"] == want, "SPRING_MIST_FOREST_TEMPLATE_PIN:" + label)
        helpers[label] = helper
    template = helpers["footing_wards"]._template(fixture, helpers, compose)
    engine = native / "mage_water_chain"
    common = _module(engine / "__init__.py", "union22_spring_mist_forest_shared_cases")
    shared_cases = compose.read_file(engine / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA, "SPRING_MIST_FOREST_SHARED_CASES")
    cases = {}
    for label, want in CASE_PINS.items():
        raw = compose.read_file((native if "/" in label else HERE) / label)
        fixtures[label] = compose.identity(raw)
        compose.need(fixtures[label]["sha256"] == want, "SPRING_MIST_FOREST_CASE_PIN:" + label)
        cases[label] = raw.decode("utf-8")
    shared_cases = shared_cases.decode("utf-8")
    art_cases = cases.pop("forest_cases.luau")
    compose.need(art_cases.count(FIELD_INSERT) == 1, "SPRING_MIST_FOREST_FIELD_INSERT")
    runes = cases.pop("builder_forms/zombie_rune_cases.luau")
    old_beast = cases.pop("ninja_beast_castle/beast_cases.luau")
    compose.need(runes.endswith("end\n") and old_beast.endswith("end\n"), "SPRING_MIST_FOREST_CASE_BOUNDARY")
    zombie = runes.removesuffix("end\n") + cases.pop("zombie_cases.luau") + "\nend\n"
    beast = old_beast.removesuffix("end\n") + cases.pop("beast_cases.luau") + "\nend\n"
    game_cases = "\n".join((shared_cases, *cases.values(), beast, zombie))

    sources = profile["sources"]
    stages = tuple(compose.RECENT_TRIAL_STAGES)
    compose.need(stages.count(FOLLOWUP) == 1, "SPRING_MIST_FOREST_PROFILE_STAGE")
    index = stages.index(FOLLOWUP)
    after = (compose.trial_sources_before(profile, stages[index - 1]) if index else
             {name: row["after"] for name, row in sources.items()})
    before = compose.trial_sources_before(profile, FOLLOWUP)
    changed = profile[FOLLOWUP]["rows"]
    scope = {FIELD_ART, *(routes[name] for name in ("Host", "SevenRoleCombat", "InteractionGuard",
             "InvulRuntime", "SwarmCombat"))}
    compose.need(set(changed) == scope
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] == before[name] for name, row in changed.items())
                 and {name for name in after if after[name] != before[name]} == scope, "SPRING_MIST_FOREST_PROFILE_SCOPE")
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    off_root = source_root.parent / compose.SPRING_MIST_FOREST_OFF / "sources"

    generated = {}
    for name, art_name, root in ((ON_PROGRAM, ART_ON_PROGRAM, source_root),
                                 (OFF_PROGRAM, ART_OFF_PROGRAM, off_root)):
        bodies = common._sources(root, pins[name], compose)
        generated[name] = common._program(bodies, routes, template, game_cases, compose)
        # The authored art fixture hooks mock property changes. Keep that
        # fixture scoped to the separate art program, with the same source pins.
        art = art_cases.replace(FIELD_INSERT, bodies[FIELD_ART], 1)
        generated[art_name] = common._program(bodies, routes, template, shared_cases + "\n" + art, compose)
    return generated, pins, fixtures


def _args(case, binary):
    if case in ART_CASES:
        name = ART_OFF_PROGRAM if case in OFF_CASES else ART_ON_PROGRAM
    else:
        name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "SPRING_MIST_FOREST_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "SPRING_MIST_FOREST_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        lines = stdout.replace(b"\r\n", b"\n").split(b"\n")
        compose.need(stderr == b"" and status == b"0\n", "SPRING_MIST_FOREST_RESULT:" + case)
        evidence = {}
        if case in ART_CASES:
            compose.need(len(lines) == 4 and lines[0] == ART_BUDGET and lines[1].startswith(b"ART_ROUTE\t")
                         and compose.identity(lines[1]) == ART_ROUTES, "SPRING_MIST_FOREST_ART_METRICS:" + case)
            evidence = {"visual_budget": lines[0].decode("ascii"), "route_geometry": compose.identity(lines[1])}
            lines = lines[2:]
        compose.need(lines == [marker.encode("utf-8"), b""], "SPRING_MIST_FOREST_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status), **evidence}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED",
            "art": "NOT_TESTED", "gpu": "NOT_MEASURED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "SPRING_MIST_FOREST_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "SPRING_MIST_FOREST_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "SPRING_MIST_FOREST_OUTPUT")
    prepared = _prepare(source_root, profile, compose)
    output.mkdir()
    for name, raw in prepared[0].items():
        (output / name).write_bytes(raw)
    for case in EXPECTED:
        _binary(binary, binary_pin, compose)
        result = subprocess.run([str(binary.resolve()), *_args(case, binary)[1:]], cwd=output.parent,
                                capture_output=True, env=environment, timeout=110)
        (output / f"{case}.stdout.log").write_bytes(result.stdout)
        (output / f"{case}.stderr.log").write_bytes(result.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{result.returncode}\n".encode("ascii"))
        compose.need(result.returncode == 0, "SPRING_MIST_FOREST_EXIT:" + case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
