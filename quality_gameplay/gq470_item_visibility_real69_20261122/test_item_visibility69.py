"""Strict current #1010 PREP, including two exact-body Luau lifecycle processes."""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import patch_item_visibility69 as patch

CASE_NAMES = ("item_visibility_three_roles", "item_world_limit_and_zero_key", "egg_arena_limit_and_zero_key",
              "castle_station_marked_removal", "boss_marked_removal")

# This API double exercises the actual registered complete body and its immediate preimage.
# Instance lifetime is synchronous here. Roblox scheduling, rendering, and real pickup inputs are outside this fixture.
FIXTURE = r'''
local function signal()
    local listeners = {}
    local event = {}
    function event:Connect(callback)
        local connection = {}
        listeners[connection] = callback
        function connection:Disconnect()
            listeners[self] = nil
        end
        return connection
    end
    function event:Fire()
        for _, callback in pairs(listeners) do callback() end
    end
    function event:Count()
        local count = 0
        for _ in pairs(listeners) do count += 1 end
        return count
    end
    return event
end

local function instance(class)
    local children, signals = {}, {}
    local object = {Name=class, ClassName=class, CanQuery=true, Transparency=0, Destroying=signal(),
                    Size={X=1,Y=1,Z=1}, Color={}}
    function object:IsA(name)
        return name == class or (name == "BasePart" and (class == "Part" or class == "WedgePart"))
    end
    function object:GetChildren()
        local live = {}
        for _, child in ipairs(children) do
            if child.Parent == self then table.insert(live, child) end
        end
        return live
    end
    function object:GetDescendants()
        local descendants = {}
        for _, child in ipairs(self:GetChildren()) do
            table.insert(descendants, child)
            for _, member in ipairs(child:GetDescendants()) do table.insert(descendants, member) end
        end
        return descendants
    end
    function object:FindFirstChild(name)
        for _, child in ipairs(self:GetChildren()) do
            if child.Name == name then return child end
        end
        return nil
    end
    function object:GetPropertyChangedSignal(name)
        if not signals[name] then signals[name] = signal() end
        return signals[name]
    end
    function object:SetAttribute() end
    function object:Adopt(child) table.insert(children, child) end
    function object:Destroy()
        if self.destroyed then return end
        self.destroyed = true
        self.Destroying:Fire()
        for _, child in ipairs(self:GetChildren()) do child:Destroy() end
        self.Parent = false
    end
    return setmetatable(object, {__newindex=function(self, name, value)
        if name == "Parent" and value then value:Adopt(self) end
        rawset(self, name, value)
    end})
end

local frame = setmetatable({}, {__mul=function(a) return a end})
local function set(node, name, value)
    node[name] = value
    node:GetPropertyChangedSignal(name):Fire()
end

local function add(parent, class, name)
    local node = instance(class)
    node.Name, node.Parent, node.CFrame = name, parent, frame
    return node
end

local function checkParts(anchor, folder, count)
    local parts = assert(anchor:FindFirstChild(folder), folder):GetChildren()
    assert(#parts == count)
    for _, part in ipairs(parts) do
        local weld = assert(part:FindFirstChild("WeldConstraint"))
        assert(part:IsA("BasePart") and not part.CanCollide and not part.CanTouch and not part.CanQuery
               and part.Massless and weld.Part0 == anchor and weld.Part1 == part)
    end
    return parts
end

local function runItemCleanup(mode, source)
    local workspace = instance("Workspace")
    local listeners = {}
    workspace.DescendantAdded = {Connect=function(_, callback) table.insert(listeners, callback) end}
    local function dispatch(node)
        for _, callback in ipairs(listeners) do callback(node) end
    end
    local services = {RunService={IsStudio=function() return true end}, Players={}, TweenService={}, Debris={}}
    local enum = setmetatable({}, {__index=function(_, kind)
        return setmetatable({}, {__index=function(_, value) return kind .. "." .. value end})
    end})
    local colors = function(r,g,b) return {r,g,b} end
    local evaluate = assert(loadstring(source ..
        "\nreturn {eggs=activeEggs, items=activeItems, marked=marked}"))
    setfenv(evaluate, setmetatable({
        game={GetService=function(_, service) return assert(services[service]) end},
        workspace=workspace, Instance={new=instance}, Enum=enum,
        CFrame={new=function() return frame end, Angles=function() return frame end},
        Vector3={new=function(x,y,z) return {X=x,Y=y,Z=z} end},
        Color3={fromRGB=colors}, task={defer=function(fn) fn() end}, print=function() end,
    }, {__index=getfenv()}))
    local state = evaluate()
    assert(#listeners == 1 and (mode == "off" or mode == "on"))
    local previous = mode == "off"
    local function report(name)
        print("CASE", name, if previous then "EXPECTED_BASELINE_REMAINDER" else "PASS")
    end
    local preview = add(workspace, "Model", "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW")
    local team = add(preview, "Model", "TEAM_Arena")
    local br = add(preview, "Model", "BATTLE_ROYALE_Arena")
    local standalone = add(workspace, "Model", "EGGRUMBLE_ItemPreviewWorld")
    local itemFolder = "EGGRUMBLE_FieldItemVisual_VisualOnly"

    for index, role in ipairs({"HEAL", "DASH", "SHIELD"}) do
        local host = ({team, br, standalone})[index]
        local item = add(host, "Part", "ITEM_1_" .. role)
        local prompt = add(item, "ProximityPrompt", "OriginalPickup")
        if index == 3 then item.CanQuery=false; item.Transparency=1 end
        dispatch(item)
        dispatch(item)
        local trim = checkParts(item, itemFolder, 2)
        local function both(alpha)
            assert(trim[1].Transparency == alpha and trim[2].Transparency == alpha)
        end
        both(if index == 3 then 1 else 0)
        set(item, "Transparency", 1)
        set(item, "CanQuery", false)
        set(item, "Transparency", 0)
        both(1)
        set(item, "CanQuery", true)
        both(0)
        assert(prompt.Parent == item and state.marked[item])
        assert(item:GetPropertyChangedSignal("Transparency"):Count() == 1
               and item:GetPropertyChangedSignal("CanQuery"):Count() == 1)
        item:Destroy()
        assert(not state.marked[item] and not trim[1].Parent and not trim[2].Parent)
        assert(item:GetPropertyChangedSignal("Transparency"):Count() == 0
               and item:GetPropertyChangedSignal("CanQuery"):Count() == 0)
        assert(state.items[host] == (if previous then 0 else nil))
    end
    print("CASE", "item_visibility_three_roles", "PASS")

    local items = {}
    for index=1,13 do
        items[index] = add(team, "Part", "ITEM_" .. index .. "_HEAL")
        dispatch(items[index])
        assert((items[index]:FindFirstChild(itemFolder) ~= nil) == (index <= 12))
    end
    local brItem = add(br, "Part", "ITEM_2_DASH")
    dispatch(brItem)
    items[1]:Destroy()
    dispatch(items[13])
    assert(state.items[team] == 12 and state.items[br] == 1)
    for _, item in ipairs(items) do item:Destroy() end
    assert(state.items[team] == (if previous then 0 else nil) and state.items[br] == 1)
    brItem:Destroy()
    report("item_world_limit_and_zero_key")

    local eggs = {}
    for index=1,29 do
        eggs[index] = add(team, "Part", "FieldEgg_" .. index)
        dispatch(eggs[index])
    end
    local brEgg = add(br, "Part", "ReleasedEgg_1")
    dispatch(brEgg)
    assert(state.eggs[team] == 28 and state.eggs[br] == 1 and not state.marked[eggs[29]])
    eggs[1]:Destroy()
    dispatch(eggs[29])
    assert(state.eggs[team] == 28 and state.marked[eggs[29]])
    for _, egg in ipairs(eggs) do egg:Destroy() end
    assert(state.eggs[team] == (if previous then 0 else nil) and state.eggs[br] == 1)
    brEgg:Destroy()
    report("egg_arena_limit_and_zero_key")

    for _, name in ipairs({"EggVault","OwnEggDeposit"}) do
        local station = add(team, "Part", name)
        local original = add(station, "ProximityPrompt", "OriginalStation")
        dispatch(station)
        dispatch(station)
        checkParts(station, "EGGRUMBLE_CastleEggStationArt_VisualOnly", 1)
        assert(state.marked[station] and original.Parent == station)
        station:Destroy()
        assert(state.marked[station] == (if previous then true else nil))
    end
    report("castle_station_marked_removal")

    local boss = add(workspace, "Model", "NEUTRAL_BOSS_STONE_GIANT")
    add(boss, "Part", "Torso")
    add(boss, "Part", "Head")
    local core = add(boss, "Part", "CoreWeakpoint")
    local prompt = add(core, "ProximityPrompt", "PreviewAttack")
    dispatch(boss)
    dispatch(core)
    local trim = assert(boss:FindFirstChild("EGGRUMBLE_StoneGiantVisual_VisualOnly"))
    assert(#trim:GetChildren() == 17 and state.marked[boss] and prompt.Parent == core)
    boss:Destroy()
    assert(state.marked[boss] == (if previous then true else nil))
    report("boss_marked_removal")
end
'''.encode()


def expected_stdout(mode):
    rows = [f"CASE\t{name}\t{'EXPECTED_BASELINE_REMAINDER' if mode == 'off' and index else 'PASS'}"
            for index, name in enumerate(CASE_NAMES)]
    return ("\n".join(rows) + "\n").encode()


def native_checks(work, native_dir):
    out = work / "native"
    out.mkdir()
    artifact = work / "original-actions.zip"
    raw = artifact.read_bytes()
    patch.require(patch.identity(raw) == {key: patch.ARTIFACT[key] for key in ("bytes", "sha256")}, "NATIVE_PARENT_ZIP")
    _, _, parent, _ = patch.verify_parent(patch.read_zip(raw))
    current = parent | {patch.TARGET_FILE: patch.registered_cleanup(parent[patch.TARGET_FILE], patch.REGISTERED.read_bytes())}
    binary = native_dir / "luau"
    compiler = native_dir / "luau-compile"
    pin = patch.identity(binary.read_bytes())
    compiler_pin = patch.identity(compiler.read_bytes())
    runner_pin = patch.identity(Path(__file__).read_bytes())
    receipts = {}
    for mode, expected in (("off", parent), ("on", current)):
        profile = work / (mode.upper() + "69")
        body_path = profile / patch.TARGET_FILE
        source = body_path.read_bytes()
        patch.require(source == expected[patch.TARGET_FILE] and b"]====]" not in source, "NATIVE_BODY")
        patch.require({file.relative_to(profile).as_posix() for file in (profile / "sources").rglob("*") if file.is_file()}
                      == set(expected), "NATIVE_69_MEMBERS")
        for name, body in expected.items():
            path = profile / name
            patch.require(path.read_bytes() == body, "NATIVE_69_BODY")
            subprocess.run([compiler, "--text", path], check=True, stdout=subprocess.DEVNULL, timeout=25)
        case = out / mode
        case.mkdir()
        prefix = FIXTURE + f'\nrunItemCleanup("{mode}", [====[\n'.encode()
        generated = prefix + source + b"]====])\n"
        program = case / "generated.luau"
        program.write_bytes(generated)
        process = subprocess.run([binary, program], capture_output=True, timeout=30)
        (case / "stdout.log").write_bytes(process.stdout)
        (case / "stderr.log").write_bytes(process.stderr)
        if process.returncode != 0 or process.stdout != expected_stdout(mode) or process.stderr:
            observation = {
                "mode": mode, "returncode": process.returncode, "compiled_sources": len(expected),
                "expected_stdout": patch.identity(expected_stdout(mode)), "stdout": patch.identity(process.stdout),
                "stderr": patch.identity(process.stderr), "native_f46": pin, "fixture": patch.identity(FIXTURE),
                "source": patch.identity(source), "generated": patch.identity(generated),
                "bounded_stdout_text": process.stdout[:3072].decode("utf-8", "replace"),
                "bounded_stderr_text": process.stderr[:3072].decode("utf-8", "replace"),
            }
            print("ITEM_CLEANUP_NATIVE_FAILURE " + json.dumps(observation, ensure_ascii=True, sort_keys=True),
                  file=sys.stderr, flush=True)
        patch.require(process.returncode == 0 and process.stdout == expected_stdout(mode) and not process.stderr
                      and patch.identity(binary.read_bytes()) == pin and program.read_bytes() == generated
                      and body_path.read_bytes() == source, "NATIVE_EXACT_LIFECYCLE_VECTOR:" + mode)
        receipts[mode] = {"selected_source": patch.identity(source), "source_range": [len(prefix), len(prefix)+len(source)],
                          "program": patch.identity(generated), "stdout": patch.identity(process.stdout),
                          "stderr": patch.identity(process.stderr), "exit": process.returncode}
    patch.require(patch.identity(compiler.read_bytes()) == compiler_pin, "NATIVE_COMPILER_DRIFT")
    result = {"scope": "A_ONLY_API_DOUBLE", "native_f46": pin, "luau_compiler": compiler_pin,
              "runner": runner_pin, "fixture": patch.identity(FIXTURE),
              "runs": receipts, "candidate_pass": 5, "baseline_control_pass": 1, "expected_baseline_remainders": 4,
              "compile_count": 138, "actual_luau_executions": 2, "studio": "NOT_TESTED"}
    (out / "receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


class TestCurrentArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = Path(os.environ["GQ470_REAL69_ZIP"])
        raw = cls.artifact.read_bytes()
        cls.contents = patch.read_zip(raw)
        cls.source = patch.verify_parent(cls.contents)[2]
        cls.new = patch.REGISTERED.read_bytes()

    def repin_nested(self, path, value):
        contents = self.contents | {path: value}
        manifest = patch.strict_json(contents[patch.MANIFEST])
        manifest["files"][path] = patch.identity(value)
        return contents | {patch.MANIFEST: json.dumps(manifest).encode()}

    def test_current_run_artifact_exact_pin_and_326(self):
        self.assertEqual(patch.identity(self.artifact.read_bytes()),
                         {key: patch.ARTIFACT[key] for key in ("bytes", "sha256")})
        self.assertEqual(len(self.contents), 326)
        self.assertEqual(len(self.source), 69)

    def test_current_route_four_hunks_and_appearance_budget(self):
        before = self.source[patch.TARGET_FILE]
        self.assertEqual(patch.registered_cleanup(before, self.new), self.new)
        self.assertEqual(len(self.new) - len(before), 238)
        for token in (b'Instance.new(', b'task.wait', b'jewel(trim,item,', b'transparencyConnection:Disconnect()',
                      b'queryConnection:Disconnect()', b'GQ470_FB015_PICKUP_ORNAMENT_VISIBILITY_REAL69_20261122'):
            self.assertEqual(before.count(token), self.new.count(token), token)

    def test_wrong_registered_candidate_rejected(self):
        with self.assertRaisesRegex(ValueError, "REGISTERED_SOURCE_PAIR"):
            patch.registered_cleanup(self.source[patch.TARGET_FILE], self.new + b"\n")

    def test_already_applied_candidate_rejected(self):
        with self.assertRaisesRegex(ValueError, "REGISTERED_SOURCE_PAIR"):
            patch.registered_cleanup(self.new, self.new)

    def test_stale_official_admission_rejected_even_with_matching_manifest(self):
        old = patch.strict_json(self.contents[patch.ADMISSION])
        old["official_build_head"] = "f6c9a503361e95eb6b166c2123ec3d18f8b5c9fc"
        with self.assertRaisesRegex(ValueError, "OFFICIAL_ADMISSION"):
            patch.verify_parent(self.repin_nested(patch.ADMISSION, json.dumps(old).encode()))

    def test_candidate_receipt_rejected_even_with_matching_manifest(self):
        old = patch.strict_json(self.contents[patch.RECEIPT])
        old["canonical_build"] = False
        with self.assertRaisesRegex(ValueError, "OFFICIAL_RECEIPT"):
            patch.verify_parent(self.repin_nested(patch.RECEIPT, json.dumps(old).encode()))

    def test_other_source_mutation_rejected_even_with_matching_manifest(self):
        other = next(name for name in self.source if name != patch.TARGET_FILE)
        with self.assertRaisesRegex(ValueError, "SOURCE_HASHES"):
            patch.verify_parent(self.repin_nested(other, self.source[other] + b"\n"))

    def test_opaque_parent_archive_tamper_rejected(self):
        archive = next(name for name in self.contents if name.startswith("legacy_rollbacks/")
                       or name.startswith("prior_boundary/legacy_rollbacks/"))
        with self.assertRaisesRegex(ValueError, "PARENT_MANIFEST_325"):
            patch.verify_parent(self.contents | {archive: b"unexpected"})

    def test_duplicate_and_traversal_paths_rejected(self):
        for entries in (("a", "a"), ("../outside",)):
            raw = io.BytesIO()
            with zipfile.ZipFile(raw, "w") as archive:
                for index, path in enumerate(entries):
                    archive.writestr(zipfile.ZipInfo(path, (2026, 1, 1, 0, 0, index*2)), b"data")
            with self.subTest(entries=entries), self.assertRaisesRegex(ValueError, "UNSAFE_ZIP"):
                patch.read_zip(raw.getvalue())

    def test_compose_changes_one_and_only_one(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            result = patch.patch_artifact(self.artifact, out)
            self.assertFalse(result["formal_rc_adoption"])
            changes = [name for name, body in self.source.items()
                       if (out / "ON69" / name).read_bytes() != (out / "OFF69" / name).read_bytes()]
            self.assertEqual(changes, [patch.TARGET_FILE])
            self.assertEqual((out / "ON69" / patch.TARGET_FILE).read_bytes(), self.new)

    def test_repacked_zip_pin_rejected_before_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            artifact = out / "rewrapped.zip"
            with zipfile.ZipFile(artifact, "w") as archive:
                for name, data in self.contents.items():
                    archive.writestr(name, data)
            with self.assertRaisesRegex(ValueError, "OFFICIAL_ZIP_PIN"):
                patch.patch_artifact(artifact, out)

    def test_expected_vectors_are_complete_and_distinct(self):
        self.assertEqual(len(expected_stdout("off").splitlines()), 5)
        self.assertEqual(expected_stdout("off").count(b"EXPECTED_BASELINE_REMAINDER"), 4)
        self.assertEqual(expected_stdout("on").count(b"\tPASS"), 5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-dir", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    native_checks(args.work, args.native_dir)
