"""Execute selected combat damage and the PRIVATE HUD before and after FB-002."""
from pathlib import Path
import subprocess

FILES = {"generated.luau", "stdout.log", "stderr.log", "receipt.json"}
EXPECTED = b"PRIVATE_FB002_EXACT_COMBAT_TO_RENDER_SPAWN_ROUND_MODES_PASS\n"
PROGRAM_ARG = "fractional_hp/generated.luau"
MODULES = {"AttackGeometry": "AttackGeometry", "CombatBalance": "Balance",
           "BasicMobilityPolicy": "Mobility", "PassiveRegenPolicy": "HealthPolicy"}


def region(raw, first, last, compose):
    compose.need(raw.count(first) == raw.count(last) == 1
                 and raw.index(first) < raw.index(last), "FRACTIONAL_HP_NATIVE_BOUNDARY")
    return raw[raw.index(first):raw.index(last)]


def program(root, lock, compose):
    followup = lock["fractional_hp_followup"]
    fixture = followup["native_fixture"]
    template = compose.read_file(compose.REPO / fixture["path"])
    marker = b"__SELECTED_FUNCTIONS__"
    compose.need(compose.identity(template) == {key: fixture[key] for key in ("bytes", "sha256")}
                 and template.count(marker) == 1, "FRACTIONAL_HP_NATIVE_FIXTURE")
    pins = {}

    def selected(name, pin, path):
        raw = compose.read_file(path)
        compose.need(compose.identity(raw) == pin, "FRACTIONAL_HP_NATIVE_SOURCE:" + name)
        pins[name] = pin
        return raw

    functions = []
    for leaf, variable in MODULES.items():
        route = f"ServerScriptService/EGGRUMBLE_{leaf}.luau"
        raw = selected(leaf, lock["sources"][route]["after"], root / route)
        functions.extend((f"local {variable}=(function()".encode(), raw, b"end)()"))
    route = "ServerScriptService/EGGRUMBLE_SevenRoleCombat.luau"
    combat = selected("SevenRoleCombat", lock["sources"][route]["after"], root / route)
    functions.extend((
        region(combat, b"local function rootAdvance(", b"local function lineClear(", compose),
        region(combat, b"local function hitHumanHeroes(", b"local function neutralAndBotHit(", compose),
    ))
    route = compose.HUD_SOURCE
    old = (root.parent / compose.FRACTIONAL_HP_OFF / "sources" / route)
    programs = []
    for name, path, pin in (
        ("baseline", old, followup["rows"][route]["parent"]["after"]),
        ("candidate", root / route, lock["sources"][route]["after"]),
    ):
        raw = selected(name, pin, path)
        render = region(raw, b"local elapsed=0\nRunService.RenderStepped:Connect(function(dt)\n",
                        b"-- GQ8_RC85_RC86_LEGACY_EXPLORE_DISCOVERY_TOAST_REAL69_20261120", compose)
        programs.extend((f"local function {name}(fixed,requireFixed)".encode(),
                         template.replace(marker, b"\n".join((*functions, render))), b"end"))
    programs.extend((
        b"baseline(false,false)",
        b"local ok,why=pcall(baseline,false,true)",
        b'assert(not ok and string.find(why,"LIVING_HP_DISPLAYED_AS_KO",1,true),"OLD_HP_CONTROL_NOT_RED")',
        b"candidate(true,true)",
        b'print("PRIVATE_FB002_EXACT_COMBAT_TO_RENDER_SPAWN_ROUND_MODES_PASS")',
    ))
    return b"\n".join(programs), pins


def observe(root, output, binary, binary_pin, context, lock, compose):
    generated, pins = program(root, lock, compose)
    stdout = compose.read_file(output / "stdout.log")
    compose.need(compose.read_file(output / "generated.luau") == generated
                 and stdout.replace(b"\r\n", b"\n") == EXPECTED
                 and not compose.read_file(output / "stderr.log")
                 and compose.identity(compose.read_file(binary)) == binary_pin, "FRACTIONAL_HP_NATIVE_RESULT")
    return {"status": "PASS", "context": context, "binary": binary_pin,
            "argv": [str(binary), PROGRAM_ARG], "source_pins": pins,
            "generated": compose.identity(generated), "stdout": compose.identity(stdout),
            "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def run(root, output, binary, binary_pin, context, lock, compose, environment):
    generated, _ = program(root, lock, compose)
    output.mkdir()
    dest = output / "generated.luau"
    dest.write_bytes(generated)
    result = subprocess.run([str(Path(binary).resolve()), PROGRAM_ARG], cwd=output.parent,
                            capture_output=True, env=environment, timeout=30)
    (output / "stdout.log").write_bytes(result.stdout)
    (output / "stderr.log").write_bytes(result.stderr)
    compose.need(result.returncode == 0, "FRACTIONAL_HP_NATIVE_EXIT")
    compose.write_json(output / "receipt.json",
                       observe(root, output, Path(binary), binary_pin, context, lock, compose))
