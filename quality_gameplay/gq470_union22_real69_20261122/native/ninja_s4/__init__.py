"""Check real PRIVATE Ninja loadout and S4 costumes against the immediate rollback."""
import importlib.util
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "ninja_s4"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
ART = "ServerScriptService/EGGRUMBLE_HeroSilhouetteArt.server.luau"
FIRST90 = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
GROWTH_SHA = "5c2487677719af031f950e0964c9c0659f9cbdd5166589f8820cfe30d885073c"
UI_ENGINE_SHA = "cdad94fb6cfedff7ed4a6bc185392f998629b62177349e41afc926fea907564b"
CASE_INPUTS = {
    "ninja_cases.luau": "f557125f73f57ca628bcc89a6bb5552ea8285d45d8d70c516888e056ad2e31ef",
    "s4_cases.luau": "1dca2db649fba85efa2cc3622aed85dabe29a39787067b806da27121c2131bc4",
}
EXPECTED = {
    "ninja_hud_transition": "real Ninja lobby opt-in and HUD D performs move then smoke; next match same HUD falls back to traditional B",
    "ninja_components": "original A damages its neutral, real B moves, and C places smoke with separate Swarm clocks",
    "ninja_off_live": "OFF retires pending D and grants only original A/B/C to the current live opted-in Ninja",
    "ninja_prompt_gates": "actual proximity prompt restricts enrollment to the Ninja lobby before READY",
    "ninja_br": "same selected Tool and physical arena constraints execute in actual BR host",
    "ninja_off_boot": "initial flag OFF disables the lobby option and grants physical original Ninja A/B/C",
    "ninja_physical_off": "immediate parent has no optional Ninja prompt/Tool D and actual legacy B still moves without spending energy",
    **{f"s4_role_{role}": f"{role} keeps original parts and gains only its defined S4 geometry; B1/B3/KO independent"
       for role in ("WARRIOR", "MAGE", "NINJA", "TRAPPER", "BUILDER", "BEAST", "ZOMBIE")},
    "s4_actual_growth": "Host/Swarm actual 180.12 active seconds gives S4, MAGE shape changes and B1/KO0 still visible",
    "s4_retirement": "actual NINJA source: downed/dead, outside field, OFF, old-avatar callbacks and Host finish restore original rig",
    "s4_physical_off": "exact original rollback retains original Warrior silhouette even during published S4",
}
OFF_CASES = {"ninja_physical_off", "s4_physical_off"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}

NINJA_PHYSICAL_OFF = """
function growthCases.ninja_physical_off()
 local stand=scenes:FindFirstChild('ROLE_NINJA')
 for _,prompt in ipairs(stand:GetChildren()) do
  check(not prompt:IsA('ProximityPrompt') or prompt.ActionText~='装備する','exact parent has no optional Ninja loadout prompt')
 end
 local session=ready('PRIVATE_NINJA_PHYSICAL_OFF','NINJA')
 check(session.ninjaLoadouts==nil,'exact parent has no Ninja loadout match snapshot')
 local original=nil
 for _,item in ipairs(player:FindFirstChildOfClass('Backpack'):GetChildren()) do
  if item:IsA('Tool')then
   local id=item:GetAttribute('EGGRUMBLE_InternalToolId')
   check(type(id)~='string' or not id:match('^EGGRUMBLE_SKILL_D_'),'physical original has no D')
   if item.Name=='技B・風走り' then original=item end
  end
 end
 check(original~=nil,'physical original owns legacy B')
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local origin=floor.Position+Vector3.new(170,floor.Size.Y*.5+3,-115)
 rootPart.CFrame=CFrame.lookAt(origin,origin+Vector3.new(1,0,0))
 humanoid.FloorMaterial=Enum.Material.Grass
 advanceTo(now+.39)
 activate(player,'B')
 check((rootPart.Position-origin).Magnitude>24 and session.swarm.getRoleGrowthSnapshot(player).energy==100,
       'original B actually moves without the optional growth debit')
 return 'immediate parent has no optional Ninja prompt/Tool D and actual legacy B still moves without spending energy'
end
"""


def _replace_once(source, old, new, compose):
    compose.need(source.count(old) == 1, "NINJA_S4_FIXTURE_BOUNDARY")
    return source.replace(old, new, 1)


def _fixture(raw, ui, compose):
    # Amend only the Native harness. The production source bodies stay selected and exact.
    replacements = (
        ("-- RANGE:BasicMobilityPolicy", ui + "\n-- RANGE:BasicMobilityPolicy"),
        ("local function ready(label)\n local count=#capturedSessions\n"
         " trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')\n",
         "local function ready(label,role,duringQueue)\n local count=#capturedSessions\n"
         " trigger(player,scenes:FindFirstChild('ROLE_'..(role or 'MAGE')),'職業選択')\n"),
        (" local entered=now\n advanceTo(entered+11.99);equal(#capturedSessions,count,'actual READY countdown not shortened')",
         " local entered=now\n if duringQueue then duringQueue() end\n"
         " advanceTo(entered+11.99);equal(#capturedSessions,count,'actual READY countdown not shortened')"),
        ("function growthCases.readySoloBR()\n local count=#capturedSessions\n"
         " trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')\n",
         "function growthCases.readySoloBR(role)\n local count=#capturedSessions\n"
         " trigger(player,scenes:FindFirstChild('ROLE_'..(role or 'MAGE')),'職業選択')\n"),
        ("\nloadingModule='Host'\n", "\nif (...)=='ninja_off_boot' then "
         "workspace:SetAttribute('P0D_ENABLE_PRIVATE_NINJA_COMBO_008',false) end\nloadingModule='Host'\n"),
        ("-- MAGE_RUNTIME_CASES\n", "-- RANGE:HeroSilhouetteArt\ndo local _=(function()\n"
         "-- SOURCE:HeroSilhouetteArt\nend)() end\nVector3.zero=Vector3.new(0,0,0)\n-- MAGE_RUNTIME_CASES\n"),
    )
    for old, new in replacements:
        raw = _replace_once(raw, old, new, compose)
    return raw


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    mage = native / "mage_water_chain"
    shared = native / "mage_projectiles"
    growth = compose.REPO / "quality_gameplay/gq470_match_role_growth_20261123/native/growth_cases.luau"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    growth_pack = compose.read_file(growth)
    audited = compose.strict_json(manifest)
    compose.need(compose.identity(manifest)["sha256"] == MANIFEST_SHA
                 and compose.identity(fixture) == audited["fixtures"]["engine_fixture.luau"]
                 and compose.identity(growth_pack)["sha256"] == GROWTH_SHA, "NINJA_S4_ENGINE_PINS")
    start, end = b"-- GQ470_SECTION_BEGIN UI_ENGINE\n", b"-- GQ470_SECTION_END UI_ENGINE\n"
    compose.need(growth_pack.count(start) == growth_pack.count(end) == 1
                 and growth_pack.index(start) < growth_pack.index(end), "NINJA_S4_UI_ENGINE_BOUNDARY")
    ui = growth_pack[growth_pack.index(start) + len(start):growth_pack.index(end)]
    compose.need(compose.identity(ui)["sha256"] == UI_ENGINE_SHA, "NINJA_S4_UI_ENGINE_PIN")

    spec = importlib.util.spec_from_file_location("union22_ninja_existing_mage_native", mage / "__init__.py")
    saved = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(saved)
    mage_cases = compose.read_file(mage / "cases.luau")
    compose.need(compose.identity(mage_cases)["sha256"] == saved.CASES_SHA, "NINJA_S4_MAGE_CASE_PIN")
    base_cases = _replace_once(mage_cases.decode("utf-8"), "function growthCases.hud_loadout_transition()",
        "growthCases.existingHudInventory=hudOnActualInventory\n\nfunction growthCases.hud_loadout_transition()", compose)

    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture), "ui": compose.identity(ui),
                "mage_cases": compose.identity(mage_cases)}
    cases = [base_cases]
    for name, sha in CASE_INPUTS.items():
        raw = compose.read_file(HERE / name)
        pin = compose.identity(raw)
        compose.need(pin["sha256"] == sha, "NINJA_S4_CASE_PIN:" + name)
        fixtures[name] = pin
        cases.append(raw.decode("utf-8"))
    cases.append(NINJA_PHYSICAL_OFF)

    routes = audited["runtime_routes"] | {"HeroSilhouetteArt": ART}
    after = {name: row["after"] for name, row in profile["sources"].items()}
    changed = profile["ninja_s4_followup"]["rows"]
    compose.need(set(changed) == {ART, FIRST90, routes["Host"], routes["SevenRoleCombat"]}
                 and all(row["parent"]["before"] == profile["sources"][name]["before"]
                         and row["parent"]["after"] != after[name] for name, row in changed.items()),
                 "NINJA_S4_PROFILE_SCOPE")
    later = profile["wing_warrior_followup"]["rows"]
    newest = profile["field_loadouts_followup"]["rows"]
    return_stage = profile["return_convert_followup"]["rows"]
    latest = profile["ground_night_followup"]["rows"]
    before = (after | {name: row["parent"]["after"] for name, row in latest.items()}
              | {name: row["parent"]["after"] for name, row in return_stage.items()}
              | {name: row["parent"]["after"] for name, row in newest.items()}
              | {name: row["parent"]["after"] for name, row in later.items()}
              | {name: row["parent"]["after"] for name, row in changed.items()})
    off_root = source_root.parent / compose.NINJA_S4_OFF / "sources"
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    template = _fixture(fixture.decode("utf-8"), ui.decode("utf-8"), compose)
    generated = {name: saved._program(saved._sources(root, pins[name], compose), routes, template, "\n".join(cases), compose)
                 for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "NINJA_S4_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "NINJA_S4_GENERATED:" + name)
    observations = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "NINJA_S4_RESULT:" + case)
        observations[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                              "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": observations, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "NINJA_S4_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "NINJA_S4_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "NINJA_S4_OUTPUT")
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
        compose.need(result.returncode == 0, "NINJA_S4_EXIT:" + case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
