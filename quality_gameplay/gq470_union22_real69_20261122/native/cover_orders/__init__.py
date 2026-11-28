"""Replay the Builder cover, Beast orders and results and their immediate physical predecessor."""
import importlib.util
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
OUTPUT_NAME = "cover_orders"
ON_PROGRAM, OFF_PROGRAM = "generated_on.luau", "generated_off.luau"
FIRST90 = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
MANIFEST_SHA = "c104296d34b986b06b5da5b153baa49d4364c82fe0a0b7aff44d2b789336748c"
CASE_PINS = {'builder_cover_cases.luau': 'ba12dbb85b496671478c4d8f59ad2775111306dc5888e3d129d848d2c97a112a',
 'beast_orders_cases.luau': '264b1748bb011aeece501413a7fd6ac24e23b91a599a381be0ab21888cccfd40',
 'result_cases.luau': '423db6912a940ab8cde345399f2b2f69b09a71bae31d4a3a381c58640e98e19f'}
EXPECTED = {'builder_cover_offer_keys': 'Builder G/X offer remains physically registered and reaches the real deck '
                             'selector',
 'cover_1': 'BUILDER-026 exact real Tool, S0 width, blocking ray, one debit, owner cap and expiry',
 'cover_2': 'BUILDER-048 exact real Tool, S0 width, blocking ray, one debit, owner cap and expiry',
 'cover_3': 'BUILDER-066 exact real Tool, S0 width, blocking ray, one debit, owner cap and expiry',
 'cover_4': 'BUILDER-072 exact real Tool, S0 width, blocking ray, one debit, owner cap and expiry',
 'cover_neutral_break': 'existing authoritative neutral swings physically break a covered player route before '
                        'TTL',
 'cover_off': 'OFF retires old wall and D Tool, same legacy Builder ABC stays',
 'cover_physical_off': 'unchanged parent Builder A/B/C and original specialized gear suit remain',
 'beast091_chase': 'actual A retasks one current server-owned companion towards a legal neutral for two '
                   'seconds',
 'beast092_return': 'actual C returns the same animal by its old MoveTo path, with no relocation shortcut',
 'beast093_guard': 'actual D posts the existing companion to a bounded guard point without changing HP',
 'beast_orders_denied': 'registered pet, neutral allegiance, cover, and carrying are all checked before debit',
 'beast_orders_late_wall': 'late wall cancels the live movement order without crossing or retaining the cue',
 'beast_orders_live_off': 'runtime OFF restores standard Tools without destroying or resummoning its '
                          'still-live companion',
 'beast_orders_same_avatar': 'a replacement player avatar cannot inherit the active old companion command',
 'beast_orders_switch': 'the same live lobby supports switching between order, Thunder, and standard decks',
 'beast_orders_physical_off': 'physical parent keeps standard BEAST and its one actual original companion',
 'result_deadline_and_manual_ready': 'deadline result, readable reason, no auto-queue, existing READY starts '
                                     'the next match',
 'result_team_castle_win': 'real castle authority selects team winner, original result retains score and a '
                           'brief replay hint',
 'result_br_castle_win': 'BR uses its distinct last-castle reason and existing no-team result'}
OFF_CASES = {"cover_physical_off", "beast_orders_physical_off"}
PROCESS_COUNT = len(EXPECTED)
FILES = {ON_PROGRAM, OFF_PROGRAM, "receipt.json"} | {
    f"{case}.{suffix}" for case in EXPECTED for suffix in ("stdout.log", "stderr.log", "status.txt")
}


def _template(raw, compose):
    text = raw.decode("utf-8")

    def exact(body, old, new):
        compose.need(body.count(old) == 1, "COVER_ORDERS_ENGINE_BOUNDARY")
        return body.replace(old, new, 1)

    text = exact(text, "-- RANGE:MatchResultService\n",
                 "local ColorSequenceKeypoint={new=function(time,color)return {Time=time,Value=color} end}\n"
                 "-- RANGE:MatchResultService\n")
    text=exact(text,"local fixturePrint=print","local fixturePrint=print;math.randomseed(12345)")
    text=exact(text,"-- MAGE_RUNTIME_CASES\n","Vector3.zero=Vector3.new(0,0,0)\n-- MAGE_RUNTIME_CASES\n")
    text=exact(text,
        "local function ready(label)\n local count=#capturedSessions\n trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')\n",
        "local function ready(label,role)\n local count=#capturedSessions\n trigger(player,scenes:FindFirstChild('ROLE_'..(role or 'MAGE')),'職業選択')\n")
    # Same GQ522 query behavior covered by the Builder author's local fixture.
    text=exact(text,'''local function queryExcluded(part,params)
 for _,object in ipairs(params.FilterDescendantsInstances or {})do
  if part==object or part:IsDescendantOf(object)then return true end
 end
 return false
end
''','''local function queryExcluded(part,params)
 local matched=false
 for _,object in ipairs(params.FilterDescendantsInstances or {}) do
  if part==object or part:IsDescendantOf(object) then matched=true;break end
 end
 return if params.FilterType==Enum.RaycastFilterType.Include then not matched else matched
end
''')
    text=exact(text,"  CanCollide=false,Anchored=false,Health=100,MaxHealth=100,FloorMaterial=Enum.Material.Concrete,",
        "  CanCollide=false,CanQuery=true,Anchored=false,Health=100,MaxHealth=100,FloorMaterial=Enum.Material.Concrete,")
    return exact(text,"local moduleRequires={}\n",'''function methods:MoveTo(at) self._nativeMoveGoal=at end

function methods:FindFirstAncestorOfClass(class)
 local object=self.Parent
 while object do
  if object.ClassName==class then return object end
  object=object.Parent
 end
 return nil
end

workspace.GetPartBoundsInRadius=function(_self,center,radius,params)
 local found={}
 for _,part in ipairs(workspace:GetDescendants()) do
  if queryEligible(part,params) then
   local distance,half=part.Position-center,part.Size*.5
   local offset=Vector3.new(math.max(0,math.abs(distance.X)-half.X),math.max(0,math.abs(distance.Y)-half.Y),
    math.max(0,math.abs(distance.Z)-half.Z))
   if offset.Magnitude<=radius then table.insert(found,part) end
  end
 end
 return found
end

local moduleRequires={}
''')


def _prepare(source_root, profile, compose):
    native = Path(compose.__file__).resolve().parent / "native"
    mage = native / "mage_water_chain"
    shared = native / "mage_projectiles"
    manifest = compose.read_file(shared / "INPUTS.json")
    fixture = compose.read_file(shared / "engine_fixture.luau")
    fixtures = {"manifest": compose.identity(manifest), "engine": compose.identity(fixture)}
    compose.need(fixtures["manifest"]["sha256"] == MANIFEST_SHA, "COVER_ORDERS_MANIFEST")
    upstream = compose.strict_json(manifest)
    compose.need(fixtures["engine"] == upstream["fixtures"]["engine_fixture.luau"], "COVER_ORDERS_ENGINE")
    template = _template(fixture, compose)

    spec = importlib.util.spec_from_file_location("union22_shared_cover_orders", mage / "__init__.py")
    shared_mage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shared_mage)
    shared_cases = compose.read_file(mage / "cases.luau")
    fixtures["mage_water_cases"] = compose.identity(shared_cases)
    compose.need(fixtures["mage_water_cases"]["sha256"] == shared_mage.CASES_SHA, "COVER_ORDERS_SHARED_CASES")
    cases = [shared_cases.decode("utf-8")]
    for label, want in CASE_PINS.items():
        path = HERE / label
        raw = compose.read_file(path)
        pin = compose.identity(raw)
        compose.need(pin["sha256"] == want, "COVER_ORDERS_CASE_PIN:" + label)
        fixtures[label] = pin
        cases.append(raw.decode("utf-8"))

    routes = upstream["runtime_routes"]
    sources = profile["sources"]
    after = {name: row["after"] for name, row in sources.items()}
    changed = profile["cover_orders_followup"]["rows"]
    must_change = {FIRST90, *(routes[name] for name in ("Host", "SwarmCombat", "SevenRoleCombat",
                                                       "InteractionGuard", "MatchResultService"))}
    compose.need(set(changed) == must_change
                 and all(row["parent"]["before"] == sources[name]["before"]
                         and row["parent"]["after"] != after[name] for name, row in changed.items()),
                 "COVER_ORDERS_PROFILE_SCOPE")
    before = compose.trial_sources_before(profile, "cover_orders_followup")
    pins = {ON_PROGRAM: after, OFF_PROGRAM: before}
    off_root = source_root.parent / compose.COVER_ORDERS_OFF / "sources"
    corpus = "\n".join(cases)
    generated = {name: shared_mage._program(shared_mage._sources(root, pins[name], compose), routes, template, corpus, compose)
                 for name, root in ((ON_PROGRAM, source_root), (OFF_PROGRAM, off_root))}
    return generated, pins, fixtures


def _args(case, binary):
    name = OFF_PROGRAM if case in OFF_CASES else ON_PROGRAM
    return [binary.name, f"{OUTPUT_NAME}/{name}", "-a", case]


def _binary(binary, pin, compose):
    compose.need(compose.identity(compose.read_file(binary)) == pin, "COVER_ORDERS_BINARY")


def _receipt(output, binary, binary_pin, context, prepared, compose):
    generated, pins, fixtures = prepared
    _binary(binary, binary_pin, compose)
    for name, raw in generated.items():
        compose.need(compose.read_file(output / name) == raw, "COVER_ORDERS_GENERATED:" + name)
    results = {}
    for case, detail in EXPECTED.items():
        stdout = compose.read_file(output / f"{case}.stdout.log")
        stderr = compose.read_file(output / f"{case}.stderr.log")
        status = compose.read_file(output / f"{case}.status.txt")
        marker = f"CASE\tGROWTH_ACCEPTANCE_{case}\tPASS\t{detail}"
        compose.need(stdout.replace(b"\r\n", b"\n") == (marker + "\n").encode("utf-8")
                     and stderr == b"" and status == b"0\n", "COVER_ORDERS_RESULT:" + case)
        results[case] = {"argv": _args(case, binary), "marker": marker, "stdout": compose.identity(stdout),
                         "stderr": compose.identity(stderr), "status": compose.identity(status)}
    return {"status": "PASS", "context": context, "binary": binary_pin, "source_pins": pins,
            "fixture_pins": fixtures, "generated": {name: compose.identity(raw) for name, raw in generated.items()},
            "cases": results, "process_count": PROCESS_COUNT, "studio": "NOT_TESTED", "android": "NOT_TESTED"}


def observe(source_root, out_folder, binary, binary_pin, context, profile, compose):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME and output.is_dir() and not output.is_symlink()
                 and {path.name for path in output.iterdir()} == FILES
                 and all(path.is_file() and not path.is_symlink() for path in output.iterdir()), "COVER_ORDERS_FILESET")
    result = _receipt(output, binary, binary_pin, context, _prepare(source_root, profile, compose), compose)
    compose.need(compose.strict_json(compose.read_file(output / "receipt.json")) == result, "COVER_ORDERS_RECEIPT")
    return result


def run(source_root, out_folder, binary, binary_pin, context, profile, compose, environment):
    source_root, output, binary = map(Path, (source_root, out_folder, binary))
    compose.need(output.name == OUTPUT_NAME, "COVER_ORDERS_OUTPUT")
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
        compose.need(result.returncode == 0, "COVER_ORDERS_EXIT:" + case)
    compose.write_json(output / "receipt.json", _receipt(output, binary, binary_pin, context, prepared, compose))
    return observe(source_root, output, binary, binary_pin, context, profile, compose)
