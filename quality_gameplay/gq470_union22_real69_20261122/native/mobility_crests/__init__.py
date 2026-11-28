"""Run the complete fixed common mobility cases on physical PRIVATE source profiles."""

import importlib.util
import inspect
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "mobility_crests"
FOLLOWUP = "mobility_crests_followup"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
PAYLOAD_PINS = {
    "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.server.luau": (
        "9ff8dae1fa51514106ebbe9e5e406ec5fae175bd6f404e7799da3fb42ebf2101",
        "7ca85ec2ee9460813f144007527af640c691468cc4957069808f1eececa332d8",
    ),
    "ServerScriptService/EGGRUMBLE_SevenRoleCombat.luau": (
        "fdb2e43ed1233449fc326baec96a079303ca97b743bd588ccb1980698ba5ecd0",
        "d890a8a0f3ca5b04528115b67b52d61748bfda4197cdfda893eb42564d5388e6",
    ),
    "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD.client.luau": (
        "ead4f14c1f7bed5bc331e581f4e58680a15bfe0cbda997b79ca2b3a67394db70",
        "8ae7d624cd2b6cd38bf8b94824ec648ee920d43b663ae82930530b6beb8ccba9",
    ),
}
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
TEMPLATE_PINS = {
    "cover_orders": "77a75f58fa180dcf872893baa15f4a86d018a280b136aa805fdd39ffa5e79089",
    "eclipse_sweep": "5ebc4bc53341994e75448ad6a09730b1a9d138cb32a4c3458f314c904a23eeb9",
    "footing_wards": "7cf80520e9ffc8a7a0b8b148d9aa93a0ac6460f6d2bf73218a5e7a3037c77b4d",
}
CASE_PINS = {
    "mobility_cases.luau": "8ff6d921b3aaef93674533d797f29deae004b159cd8349f5b00bbdca4360fcaf",
    "builder_forms/builder_transform_cases.luau": "a897d16f4c439d1d9319f3af45f217cc22857b1bc4fd6db52b3009ccffd8fd7d",
    "ninja_steps_objectives/round_case.luau": "d3072a5d33c5cbcdfe81cca4f11517ae6e2a23eb0bbcc29ce084ea427d877c47",
}
PROPERTY_FIXTURE = b'''function methods:GetPropertyChangedSignal(key)
 local signals=rawget(self,"_nativePropertySignals")
 if not signals then signals={};rawset(self,"_nativePropertySignals",signals) end
 if not signals[key] then signals[key]=signal() end
 return signals[key]
end
player._props.AncestryChanged=player._props.AncestryChanged or signal()
rootPart._props.AncestryChanged=rootPart._props.AncestryChanged or signal()
humanoid._props.Sit=false;humanoid._props.PlatformStand=false
'''
EXPECTED = {
    "mobility_menu": "actual one-stand selection equips two mobility items instead of guide items and keeps Footing",
    "mobility_shoes": "real S0 ground speed +6% for two seconds with one E30/CD18 and exact old baseline restored",
    "mobility_glide": "real S0 one VectorForce cancels only 15% of gravity during descent for one second, E30/CD20",
    "mobility_denials": "grounded glide, rising glide, airborne speed, seats, custody and leaving the legal field are denied",
    "mobility_real_custody": "actual original enemy egg pickup immediately cancels the existing speed token and effects",
    "mobility_retire_and_off": "immediate landing and death cleanup; live OFF rejects stale Tool and preserves Footing",
    "mobility_interrupted": "an outside upward impulse cannot keep descent assist, and current restraint removes the shared walk lease",
    "mobility_stage_four": "true active-time S4 reaches +14% speed for 4s and 35% descent relief for 3s",
    "mobility_cap_override": "fastest ordinary speed capped at 27 and distinct later slow keeps the sole movement ledger",
    "mobility_physical_off": "physical navigation predecessor has both prior guide tools and Footing, no motion kit",
    "transform_glide": "S3 current falling avatar gets actual VectorForce allocation below gravity and old motion returns",
    "private_round_custody": "actual PRIVATE selection→TEAM READY with AI roster→enemy egg→human deposit/score"
                            "→results/lobby→voluntary replay",
}
OFF_CASES = {"mobility_physical_off"}
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
    compose.need(stages.count(FOLLOWUP) == 1, "MOBILITY_CRESTS_STAGE")
    current = profile["sources"]
    index = stages.index(FOLLOWUP)
    after = (compose.trial_sources_before(profile, stages[index - 1]) if index else
             {name: row["after"] for name, row in current.items()})
    before = compose.trial_sources_before(profile, FOLLOWUP)
    rows = profile[FOLLOWUP]["rows"]
    scope = set(PAYLOAD_PINS)
    compose.need(len(after) == 69 and set(after) == set(before) == set(current)
                 and set(rows) == scope and {name for name in after if after[name] != before[name]} == scope,
                 "MOBILITY_CRESTS_PROFILE_SCOPE")
    compose.need(all(row["parent"]["before"] == current[name]["before"]
                     and row["parent"]["after"] == before[name] for name, row in rows.items()),
                 "MOBILITY_CRESTS_PROFILE_ROWS")
    for route, pinned in PAYLOAD_PINS.items():
        compose.need((after[route]["sha256"], before[route]["sha256"]) == pinned,
                     "MOBILITY_CRESTS_COMPOUND_SOURCE:" + route)
    return {ON_PROGRAM: after, OFF_PROGRAM: before}


def _inputs(compose):
    native = Path(compose.__file__).resolve().parent / "native"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    engine = compose.read_file(shared / "engine_fixture.luau")
    upstream = compose.strict_json(manifest)
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(engine)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "MOBILITY_CRESTS_MANIFEST")
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "MOBILITY_CRESTS_ENGINE")
    helpers = {}
    for name, expected in TEMPLATE_PINS.items():
        helper = _module(native / name / "__init__.py", "union22_mobility_crests_" + name)
        template_source = inspect.getsource(helper._template).replace("\r\n", "\n").encode("utf-8")
        fixtures[name + "_template"] = compose.identity(template_source)
        compose.need(fixtures[name + "_template"]["sha256"] == expected, "MOBILITY_CRESTS_TEMPLATE_PIN:" + name)
        helpers[name] = helper
    template = helpers["footing_wards"]._template(engine, helpers, compose)
    fixtures["rendered_template"] = compose.identity(template.encode("utf-8"))
    compose.need(fixtures["rendered_template"]["sha256"]
                 == "cd6235cb47d6b8907d16aca65f73344cb2d6519e469eab3eaa7f6a0a11818616",
                 "MOBILITY_CRESTS_EFFECTIVE_TEMPLATE")
    common = _module(native / "mage_water_chain" / "__init__.py", "union22_mobility_crests_shared_cases")
    old = compose.read_file(native / "mage_water_chain" / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(old)
    compose.need(fixtures["mage_water_cases"]["sha256"] == common.CASES_SHA, "MOBILITY_CRESTS_SHARED_CASES")
    fixtures["property_fixture"] = compose.identity(PROPERTY_FIXTURE)
    compose.need(fixtures["property_fixture"]["sha256"]
                 == "ec48566e91e7fd5fd3fd4243760c4f1f4b1af5ff48ab80cb658c5810c99bf2d2",
                 "MOBILITY_CRESTS_PROPERTY_FIXTURE")
    cases = [old, PROPERTY_FIXTURE]
    for name, expected in CASE_PINS.items():
        raw = compose.read_file((native if "/" in name else HERE) / name)
        fixtures[name] = compose.identity(raw)
        compose.need(fixtures[name]["sha256"] == expected, "MOBILITY_CRESTS_CASE_PIN:" + name)
        cases.append(raw)
    return common, upstream["runtime_routes"], template, b"\n".join(cases).decode("utf-8"), fixtures


crests = _module(HERE / "crests.py", "union22_mobility_team_crests")
PROCESS_COUNT = len(EXPECTED) + crests.PROCESS_COUNT
FILES |= crests.FILES


def _crest_args(case,binary):
    return [binary.name,f"{OUTPUT_NAME}/{crests.PROGRAMS[crests.CASES[case]]}","-a",case]


def _prepare(source_root, profile, compose):
    common, routes, template, corpus, fixtures = _inputs(compose)
    pins = _profile_pins(profile, compose)
    previous = tuple(compose.RECENT_TRIAL_STAGES).index(FOLLOWUP) > 0
    on_root = source_root.parent / compose.COMMON_HEALING_OFF / "sources" if previous else source_root
    off_root = source_root.parent / compose.MOBILITY_CRESTS_OFF / "sources"
    generated = {
        name: common._program(common._sources(root, pins[name], compose), routes, template, corpus, compose)
        for name, root in ((ON_PROGRAM, on_root), (OFF_PROGRAM, off_root))
    }
    for mode,root,pin in (("ON",on_root,pins[ON_PROGRAM]),("OFF",off_root,pins[OFF_PROGRAM])):
        generated[crests.PROGRAMS[mode]] = crests.program(root,mode,compose,pin)
    fixtures["crest_cases"] = compose.identity(compose.read_file(HERE/"crest_cases.luau"))
    fixtures["crest_fixture"] = compose.identity(compose.read_file(HERE/"crest_fixture.luau"))
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, binary_pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == binary_pin, "MOBILITY_CRESTS_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "MOBILITY_CRESTS_GENERATED:" + name)
    results = {}
    for case, text in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{text}"
        expected = (marker + "\n").encode("utf-8")
        compose.need(status == b"0\n" and stderr == b""
                     and stdout in (expected, expected.replace(b"\n", b"\r\n")),
                     "MOBILITY_CRESTS_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    for case in crests.CASES:
        stdout=compose.read_file(output/f"{case}.stdout.log")
        stderr=compose.read_file(output/f"{case}.stderr.log")
        status=compose.read_file(output/f"{case}.status.txt")
        compose.need(status==b"0\n","MOBILITY_CRESTS_CLIENT_STATUS:"+case)
        marker=crests.assert_result(case,stdout,stderr,0)
        results[case]={"argv":_crest_args(case,binary),"marker":marker,"stdout":compose.identity(stdout),
                       "stderr":compose.identity(stderr),"status":compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()),
                 "MOBILITY_CRESTS_FILESET")
    observed = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == observed,
                 "MOBILITY_CRESTS_RECEIPT")
    return observed


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "MOBILITY_CRESTS_OUTPUT")
    _binary(binary, binary_pin, compose)
    prepared = _prepare(source_root, profile, compose)
    output.mkdir()
    for name, program in prepared[0].items():
        (output / name).write_bytes(program)
    from case_batch import run_cases

    def run_case(case):
        proc = subprocess.run([str(binary.resolve()), *_args(case, binary)[1:]], cwd=output.parent,
                              capture_output=True, env=environment, timeout=90)
        (output / f"{case}.stdout.log").write_bytes(proc.stdout)
        (output / f"{case}.stderr.log").write_bytes(proc.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{proc.returncode}\n".encode("ascii"))
        compose.need(proc.returncode == 0, "MOBILITY_CRESTS_EXIT:" + case)
    run_cases(EXPECTED, run_case)

    def run_extra(case):
        _binary(binary,binary_pin,compose)
        proc=subprocess.run([str(binary.resolve()),*_crest_args(case,binary)[1:]],cwd=output.parent,
                            capture_output=True,env=environment,timeout=110)
        (output/f"{case}.stdout.log").write_bytes(proc.stdout)
        (output/f"{case}.stderr.log").write_bytes(proc.stderr)
        (output/f"{case}.status.txt").write_bytes(f"{proc.returncode}\n".encode("ascii"))
        crests.assert_result(case,proc.stdout,proc.stderr,proc.returncode)
    run_cases(crests.CASES, run_extra)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
