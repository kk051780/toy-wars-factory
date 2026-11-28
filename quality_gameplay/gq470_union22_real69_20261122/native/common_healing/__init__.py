"""Fixed healing acceptance cases over actual PRIVATE source and its physical OFF."""

import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME, FOLLOWUP = "common_healing", "common_healing_followup"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
BOT_ACTORS = "ServerScriptService/EGGRUMBLE_BotActors.luau"
BOT_ACTORS_SHA = "06e5197b826d1cd279d27ce019a92d9dcc5b9b651c6933587e69a6ecff5cdc23"
PAYLOAD_PINS = {
    "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.server.luau": (
        "ababdeef65716d1030fb4604e7be8764533a690c09ae4dc327afda3788954c92",
        "9ff8dae1fa51514106ebbe9e5e406ec5fae175bd6f404e7799da3fb42ebf2101",
    ),
    "ServerScriptService/EGGRUMBLE_SevenRoleCombat.luau": (
        "41bd9ac43cf84a228e85023fec9d621406e3692f88ca6c0b5df32307d284433d",
        "fdb2e43ed1233449fc326baec96a079303ca97b743bd588ccb1980698ba5ecd0",
    ),
}
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}
INPUT_PINS = {
    "healing_cases.luau": "e6c863d06dee4e4bdee075e294e2f7ed755f5f1cbaff3f6eda9e6f178c0107bb",
    "ninja_steps_objectives/round_case.luau": "d3072a5d33c5cbcdfe81cca4f11517ae6e2a23eb0bbcc29ce084ea427d877c47",
    "case_batch.py": "3a8a631520f750dd122e3be38f909cca77fe48050d83b20ef65023d0007e6c33",
}
EXPECTED = {
    "healing_self": "016 exact one-second channel, E40/CD28, actual 3% self heal once",
    "healing_area": "019 exact S0 radius3 plus two current allies only, 1% once, E45/CD32",
    "healing_hit": "original Humanoid TakeDamage event interrupts channel with no success",
    "healing_candidate_change": "dead, removed squad members and allies newly behind cover are independently rejected at release",
    "healing_br": "real solo BR denies TEAM heal without debit while exact self-heal still works",
    "healing_custody_off": "real hostile egg acquisition and physical live OFF cancel while Footing remains",
    "healing_tool_phase": "ownership and phase remove the focused channel before an old delayed callback",
    "healing_physical_off": "physical OFF retains mobility and Footing with no healing Tools",
    "healing_legacy_mage": "original Mage C retains its existing +25 heal through the one shared cap writer",
    "healing_stage_four": "real active S4: 7% self, 3% inside seven studs only, capped at MaxHealth",
    "private_round_custody": "actual PRIVATE selection→TEAM READY with AI roster→enemy egg→human deposit/score"
                            "→results/lobby→voluntary replay",
}
OFF_CASES = {"healing_physical_off"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def _profile_pins(profile, compose):
    stages = tuple(compose.RECENT_TRIAL_STAGES)
    compose.need(stages.count(FOLLOWUP) == 1, "COMMON_HEALING_STAGE")
    current = profile["sources"]
    index = stages.index(FOLLOWUP)
    after = (compose.trial_sources_before(profile, stages[index - 1]) if index else
             {name: row["after"] for name, row in current.items()})
    before = compose.trial_sources_before(profile, FOLLOWUP)
    rows = profile[FOLLOWUP]["rows"]
    scope = set(PAYLOAD_PINS)
    compose.need(len(after) == 69 and set(after) == set(before) == set(current)
                 and set(rows) == scope and {name for name in after if after[name] != before[name]} == scope,
                 "COMMON_HEALING_PROFILE_SCOPE")
    compose.need(all(row["parent"]["before"] == current[name]["before"]
                     and row["parent"]["after"] == before[name] for name, row in rows.items()),
                 "COMMON_HEALING_PROFILE_ROWS")
    for route, pinned in PAYLOAD_PINS.items():
        compose.need((after[route]["sha256"], before[route]["sha256"]) == pinned,
                     "COMMON_HEALING_COMPOUND_SOURCE:" + route)
    compose.need(after[BOT_ACTORS]["sha256"] == before[BOT_ACTORS]["sha256"] == BOT_ACTORS_SHA,
                 "COMMON_HEALING_BOT_FACTORY_PIN")
    return {ON_PROGRAM: after, OFF_PROGRAM: before}


def _inputs(native, compose):
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    engine = compose.read_file(shared / "engine_fixture.luau")
    upstream = compose.strict_json(manifest)
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(engine)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "COMMON_HEALING_MANIFEST")
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "COMMON_HEALING_ENGINE")
    helpers = {}
    for name, expected in TEMPLATE_PINS.items():
        helper = _module(native / name / "__init__.py", "union22_common_healing_" + name)
        src = inspect.getsource(helper._template).replace("\r\n", "\n").encode("utf-8")
        fixtures[name + "_template"] = compose.identity(src)
        compose.need(fixtures[name + "_template"]["sha256"] == expected, "COMMON_HEALING_TEMPLATE_PIN:" + name)
        helpers[name] = helper
    template = helpers["footing_wards"]._template(engine, helpers, compose)
    fixtures["rendered_template"] = compose.identity(template.encode("utf-8"))
    compose.need(fixtures["rendered_template"]["sha256"]
                 == "cd6235cb47d6b8907d16aca65f73344cb2d6519e469eab3eaa7f6a0a11818616",
                 "COMMON_HEALING_EFFECTIVE_TEMPLATE")
    common = _module(native / "mage_water_chain" / "__init__.py", "union22_common_healing_program")
    base = compose.read_file(native / "mage_water_chain" / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(base)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA, "COMMON_HEALING_SHARED_CASES")
    material = {}
    for name, expected in INPUT_PINS.items():
        root = HERE if name == "healing_cases.luau" else native
        raw = compose.read_file(root / name)
        fixtures[name] = compose.identity(raw)
        compose.need(fixtures[name]["sha256"] == expected, "COMMON_HEALING_CASE_PIN:" + name)
        material[name] = raw.decode("utf-8")
    return common, upstream["runtime_routes"], template, base.decode("utf-8"), material, fixtures


def _program(common, bodies, routes, template, base, material, compose):
    src = bodies[BOT_ACTORS]
    begin, end = "local function makePart(", "local function desiredTarget("
    marker = "-- ACTUAL_BOT_ACTOR_FACTORY"
    cases = material["healing_cases.luau"]
    compose.need(src.count(begin) == src.count(end) == cases.count(marker) == 1 and src.index(begin) < src.index(end),
                 "COMMON_HEALING_BOT_FACTORY_BOUNDARY")
    current = cases.replace(marker, src[src.index(begin):src.index(end)], 1)
    text = "\n".join((base, current, material["ninja_steps_objectives/round_case.luau"]))
    return common._program(bodies, routes, template, text, compose)


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    common, routes, template, base, material, fixtures = _inputs(native, compose)
    pins = _profile_pins(profile, compose)
    off_root = source_root.parent / compose.COMMON_HEALING_OFF / "sources"
    generated = {
        name: _program(common, common._sources(root, pins[name], compose), routes, template, base, material, compose)
        for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))
    }
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, binary_pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == binary_pin, "COMMON_HEALING_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "COMMON_HEALING_GENERATED:" + name)
    results = {}
    for case, text in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{text}"
        expected = (marker + "\n").encode("utf-8")
        compose.need(status == b"0\n" and stderr == b""
                     and stdout in (expected, expected.replace(b"\n", b"\r\n")), "COMMON_HEALING_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "COMMON_HEALING_FILESET")
    observed = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == observed, "COMMON_HEALING_RECEIPT")
    return observed


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "COMMON_HEALING_OUTPUT")
    _binary(binary, binary_pin, compose)
    prepared = _prepare(source_root, profile, compose)
    output.mkdir()
    for name, raw in prepared[0].items():
        (output / name).write_bytes(raw)
    scheduler = _module(Path(compose.__file__).resolve().parent / "native" / "case_batch.py",
                        "union22_common_healing_case_batch")

    def execute(case):
        proc = subprocess.run([str(binary.resolve()), *_args(case, binary)[1:]], cwd=output.parent,
                              capture_output=True, env=environment, timeout=90)
        (output / f"{case}.stdout.log").write_bytes(proc.stdout)
        (output / f"{case}.stderr.log").write_bytes(proc.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{proc.returncode}\n".encode("ascii"))
        compose.need(proc.returncode == 0, "COMMON_HEALING_EXIT:" + case)

    scheduler.run_cases(EXPECTED, execute)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
