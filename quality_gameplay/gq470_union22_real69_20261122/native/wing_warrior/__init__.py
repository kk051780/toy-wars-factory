"""Replay the selected PRIVATE elemental, wing and Warrior paths and physical rollback."""
import importlib.util
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "wing_warrior"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
COMBAT_FEEL = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
CASE_INPUTS = {
    "warrior_cases.luau": "996bd37da2b712134118703f1738a89fc4d391285e0ed11577348e1a3b7c879c",
    "wing_cases.luau": "3bd26a5b1e5706ea121deb1e6da6ae329fc1d05b3b2893a49d33f4c1abd07a11",
    "element_cases.luau": "88b1a1366c4a0bb89c7525d0a4c3fcea541c79168c5e6af006068c1e0af456c8",
}
EXPECTED = {
    "warrior_ignite": "existing Warrior B emits real tell; one authorized neutral strike plus bounded shared burn, E30 and cleanup",
    "warrior_ring": "actual C radial neutral hit including rear at S0, no burn, no extra hit, no hero HP change",
    "warrior_combo": "actual D has one E80 payment, period .8 warning, one unified pulse and one bounded burn registration",
    "warrior_wall_and_resist": "actual wall by impact blocks both writes; defensive neutral shares the existing immunity and no burn",
    "warrior_off": "real live feature-OFF cancels pending attack and restores ordinary Warrior A/B/C",
    "warrior_budget": "one Swarm ledger holds component B18, C22 and D40, all observed around exact charge boundaries",
    "warrior_growth_cap": "actual S4 growth then radius seven to five real neutrals, one burn ledger, teammate untouched",
    "warrior_burn_off": "real current burn stops and its remaining reserve is retired on feature OFF",
    "wing_combo": "real COMBO-005 Tool pays once, flies safely, lands, warns, and only then the original ice spear hits",
    "wing_only": "standalone flight applies a real bounded wind ring only after legal touchdown",
    "wing_negative_ceiling": "flight rejects or cleans up without a late spear: ceiling",
    "wing_negative_avatar": "flight rejects or cleans up without a late spear: avatar",
    "wing_br_steering": "BR opt-in uses its own world, bounded steering, ground and release",
    "element_fire": "actual fire projectile reserves some neutral damage for real timed burn",
    "element_fire_rollback": "OFF cancels in-flight status before delayed damage",
    "element_resistance": "actual neutral species resists status and preserves direct hit",
    "element_frost": "actual Frost hit reduces neutral ground movement; marker and slow expire",
    "element_icicle": "real icicle respects tell, captured direction, and S0 cap",
    "element_needle": "fixed needle speed and first-contact stop reach actual HP",
    "wing_warrior_physical_off": "exact parent restores both Mage and Warrior A/B/C and has no elemental, wing or Warrior opt-in",
}
OFF_CASE = "wing_warrior_physical_off"
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}

PHYSICAL_OFF = """
function growthCases.wing_warrior_physical_off()
 check(type(growthCases.wing_off_parent())=='string','original Mage physical-off case ran')
 for _,role in ipairs({'MAGE','WARRIOR'}) do
  local stand=scenes:FindFirstChild('ROLE_'..role)
  for _,prompt in ipairs(stand:GetChildren()) do
   if prompt:IsA('ProximityPrompt') then
    check(prompt.ActionText~='属性を装備' and prompt.ActionText~='風翼を装備'
      and (role~='WARRIOR' or prompt.ActionText~='装備する'),'parent has no new opt-in prompt')
   end
  end
 end
 local match=capturedSessions[#capturedSessions]
 check(match and match.isCurrentHuman(second) and second:GetAttribute('EGGRUMBLE_Role')=='WARRIOR',
    'exact parent grants already deployed other human Warrior')
 check(match.warriorLoadouts==nil,'parent has no optional Warrior loadout')
 local owned={}
 for _,tool in ipairs(second:FindFirstChildOfClass('Backpack'):GetChildren()) do
  local id=tool:GetAttribute('EGGRUMBLE_InternalToolId')
  local slot=if type(id)=='string' then id:match('^EGGRUMBLE_SKILL_([ABCD])_') else nil
  if slot then
   check(tool:GetAttribute('EGGRUMBLE_FixedAbilityId')==nil,'parent has no fixed Warrior ability ID')
   owned[slot]=true
  end
 end
 check(owned.A and owned.B and owned.C and not owned.D,'real legacy Warrior A/B/C and no D')
 return 'exact parent restores both Mage and Warrior A/B/C and has no elemental, wing or Warrior opt-in'
end
"""


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    mage = native / "mage_water_chain"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "WING_WARRIOR_MANIFEST")
    audited = compose.strict_json(manifest)
    compose.need(fixtures["engine"] == audited["fixtures"]["engine_fixture.luau"], "WING_WARRIOR_ENGINE")
    template = fixture.decode("utf-8")
    marker = "-- MAGE_RUNTIME_CASES\n"
    compose.need(template.count(marker) == 1, "WING_WARRIOR_FIXTURE_BOUNDARY")
    template = template.replace(marker, "Vector3.zero=Vector3.new(0,0,0)\n" + marker)

    spec = importlib.util.spec_from_file_location("union22_wing_shared_mage_native", mage / "__init__.py")
    reused = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reused)
    retained_cases = compose.read_file(mage / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(retained_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == reused.CASES_SHA, "WING_WARRIOR_SHARED_MAGE_CASES")
    cases = [retained_cases.decode("utf-8")]
    for name, sha in CASE_INPUTS.items():
        body = compose.read_file(HERE / name)
        pin = compose.identity(body)
        compose.need(pin["sha256"] == sha, "WING_WARRIOR_CASE_PIN:" + name)
        fixtures[name] = pin
        cases.append(body.decode("utf-8"))
    cases.append(PHYSICAL_OFF)

    routes = audited["runtime_routes"]
    after = {name: row["after"] for name, row in profile["sources"].items()}
    repair = profile["wing_warrior_followup"]
    changed = repair["rows"]
    compose.need(set(changed) == {COMBAT_FEEL, routes["Host"], routes["SwarmCombat"], routes["SevenRoleCombat"]}
                 and all(row["parent"]["before"] == profile["sources"][name]["before"]
                         and row["parent"]["after"] != after[name] for name, row in changed.items()),
                 "WING_WARRIOR_PROFILE_SCOPE")
    before = compose.trial_sources_before(profile, "wing_warrior_followup")
    off_root = source_root.parent / compose.WING_WARRIOR_OFF / "sources"
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    generated = {name: reused._program(reused._sources(root, pins[name], compose), routes, template, "\n".join(cases), compose)
                 for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case == OFF_CASE else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "WING_WARRIOR_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "WING_WARRIOR_GENERATED:" + name)
    observations = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "WING_WARRIOR_RESULT:" + case)
        observations[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                              "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": observations, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "WING_WARRIOR_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "WING_WARRIOR_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "WING_WARRIOR_OUTPUT")
    prepared = _prepare(source_root, profile, compose)
    output.mkdir()
    for name, raw in prepared[0].items():
        (output / name).write_bytes(raw)
    from case_batch import run_cases

    def run_case(case):
        _binary(binary, binary_pin, compose)
        result = subprocess.run([str(binary.resolve()), *_args(case, binary)[1:]], cwd=output.parent,
                                capture_output=True, env=environment, timeout=110)
        (output / f"{case}.stdout.log").write_bytes(result.stdout)
        (output / f"{case}.stderr.log").write_bytes(result.stderr)
        (output / f"{case}.status.txt").write_bytes(f"{result.returncode}\n".encode("ascii"))
        compose.need(result.returncode == 0, "WING_WARRIOR_EXIT:" + case)
    run_cases(EXPECTED, run_case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
