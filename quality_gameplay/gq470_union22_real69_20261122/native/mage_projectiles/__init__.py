"""Replay the fixed PRIVATE Mage launch cases on the selected Host/Combat/Swarm."""
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
INPUTS_SHA256 = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
OUTPUT_NAME = "mage_projectiles"
PROGRAM_ARG = f"{OUTPUT_NAME}/generated.luau"
PURE_CASE = "mage_projectile_stage_math"
RUNTIME_CASES = (
    "mage_cancel_avatar",
    "mage_cancel_dead",
    "mage_cancel_egg",
    "mage_cancel_end",
    "mage_cancel_leave",
    "mage_cancel_off",
    "mage_cancel_role",
    "mage_cancel_world",
    "mage_cooldown_and_energy",
    "mage_crossworld_neutral_reparent",
    "mage_legacy_tools",
    "mage_player_restraint_midflight",
    "mage_stage_energy_attributes",
    "mage_star_tell_and_nontracking",
    "mage_stone_wall_and_dodge",
    "mage_wind_hit",
    "same_round_death_respawn",
)
CASES = (*RUNTIME_CASES, PURE_CASE)
PROCESS_COUNT = len(CASES)
FILES = {"generated.luau", "receipt.json"} | {
    f"{case}.{suffix}"
    for case in CASES
    for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _pure_program(combat, test, pin, compose):
    source = combat.decode("utf-8").replace("\r\n", "\n")
    begin = "local MageProjectiles=(function()\n"
    end = "\nend)()\nlocal MageProjectileVisual=(function()"
    compose.need(source.count(begin) == source.count(end) == 1 and source.index(begin) < source.index(end),
                 "MAGE_PROJECTILES_NATIVE_PURE_BOUNDARY")
    module = source.split(begin, 1)[1].split(end, 1)[0].strip()
    compose.need(compose.identity(module.encode("utf-8")) == pin, "MAGE_PROJECTILES_NATIVE_PURE_BODY")
    require = 'local Projectile=require("./MageProjectiles")\n'
    test = test.replace("\r\n", "\n")
    compose.need(test.startswith(require), "MAGE_PROJECTILES_NATIVE_PURE_FIXTURE")
    return [f'if (...)=="{PURE_CASE}" then', "local Projectile=(function()", *module.splitlines(),
            "end)()", *test.removeprefix(require).splitlines(), "return", "end", ""]


def _program(source_root, profile, compose):
    raw_manifest = compose.read_file(HERE / "INPUTS.json")
    compose.need(compose.identity(raw_manifest)["sha256"] == INPUTS_SHA256,
                 "MAGE_PROJECTILES_NATIVE_INPUTS")
    inputs = json.loads(raw_manifest)
    compose.need(tuple(inputs["markers"]) == CASES, "MAGE_PROJECTILES_NATIVE_CASES")
    fixtures = {}
    for name, pin in inputs["fixtures"].items():
        raw = compose.read_file(HERE / name)
        compose.need(compose.identity(raw) == pin, "MAGE_PROJECTILES_NATIVE_FIXTURE:" + name)
        fixtures[name] = raw.decode("utf-8")

    source_pins = {}
    selected = {}
    routes = inputs["runtime_routes"]
    for route in [*routes.values(), *inputs["selected_only"]]:
        body = compose.read_file(source_root / route)
        pin = compose.identity(body)
        compose.need(pin == profile["sources"][route]["after"], "MAGE_PROJECTILES_NATIVE_SOURCE:" + route)
        source_pins[route] = pin
        selected[route] = body

    lines = _pure_program(selected[routes["SevenRoleCombat"]], fixtures["pure_cases.luau"],
                          inputs["pure_inline"], compose)
    ranges, declarations = {}, {}
    cases_inserted = False
    for line in fixtures["engine_fixture.luau"].splitlines():
        if line.startswith("-- RANGE:"):
            alias = line.removeprefix("-- RANGE:")
            compose.need(alias in routes and alias not in declarations, "MAGE_PROJECTILES_NATIVE_RANGE")
            declarations[alias] = len(lines)
            lines.append("")
        elif line.startswith("-- SOURCE:"):
            alias = line.removeprefix("-- SOURCE:")
            compose.need(alias in routes and alias not in ranges, "MAGE_PROJECTILES_NATIVE_BODY")
            first = len(lines) + 1
            lines.extend(selected[routes[alias]].decode("utf-8").splitlines())
            ranges[alias] = (first, len(lines))
        elif line == "-- MAGE_RUNTIME_CASES":
            compose.need(not cases_inserted, "MAGE_PROJECTILES_NATIVE_CASE_INSERTION")
            lines.extend(fixtures["cases.luau"].splitlines())
            cases_inserted = True
        else:
            lines.append(line)
    compose.need(cases_inserted and routes.keys() == ranges.keys() == declarations.keys(),
                 "MAGE_PROJECTILES_NATIVE_TEMPLATE_BOUNDARY")
    for alias, (first, last) in ranges.items():
        lines[declarations[alias]] = f"fullSourceRanges.{alias}={{first={first},last={last}}}"
    return ("\n".join(lines) + "\n").encode("utf-8"), source_pins, inputs["markers"]


def _binary_ok(binary, binary_pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == binary_pin,
                 "MAGE_PROJECTILES_NATIVE_BINARY")


def _result(output, binary, binary_pin, context, prepared, compose):
    generated, pins, markers = prepared
    _binary_ok(binary, binary_pin, compose)
    compose.need(compose.read_file(output / "generated.luau") == generated,
                 "MAGE_PROJECTILES_NATIVE_GENERATED")
    observations = {}
    for case in CASES:
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        expected_stdout = (markers[case] + "\n").encode("utf-8")
        compose.need(stdout.replace(b"\r\n", b"\n") == expected_stdout
                     and stderr == b"" and status == b"0\n",
                     "MAGE_PROJECTILES_NATIVE_RESULT:" + case)
        observations[case] = {
            "argv": [Path(binary).name, PROGRAM_ARG, "-a", case],
            "kind": "pure_stage_math" if case == PURE_CASE else "runtime_e2e",
            "marker": markers[case],
            "stdout": compose.identity(stdout),
            "stderr": compose.identity(stderr),
            "status": compose.identity(status),
        }
    return {
        "status": "PASS",
        "context": context,
        "binary": binary_pin,
        "source_pins": pins,
        "generated": compose.identity(generated),
        "process_count": PROCESS_COUNT,
        "cases": observations,
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
    }


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = Path(source_root), Path(out_folder), Path(binary)
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()),
                 "MAGE_PROJECTILES_NATIVE_FILESET")
    observed = _result(output, binary, binary_pin, context, _program(source_root, profile, compose), compose)
    compose.need(json.loads(compose.read_file(output / "receipt.json")) == observed,
                 "MAGE_PROJECTILES_NATIVE_RECEIPT")
    return observed


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = Path(source_root), Path(out_folder), Path(binary)
    compose.need(output.name == OUTPUT_NAME, "MAGE_PROJECTILES_NATIVE_OUTPUT")
    prepared = _program(source_root, profile, compose)
    generated = prepared[0]
    output.mkdir()
    (output / "generated.luau").write_bytes(generated)
    for case in CASES:
        _binary_ok(binary, binary_pin, compose)
        result = subprocess.run([str(binary.resolve()), PROGRAM_ARG, "-a", case], cwd=output.parent,
                                capture_output=True, env=environment, timeout=110)
        (output / f"{case}.stdout.log").write_bytes(result.stdout)
        (output / f"{case}.stderr.log").write_bytes(result.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{result.returncode}\n".encode("ascii"))
        compose.need(result.returncode == 0, "MAGE_PROJECTILES_NATIVE_EXIT:" + case)
    compose.write_json(output / "receipt.json", _result(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
