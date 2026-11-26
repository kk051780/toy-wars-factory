"""Artifact-free parser/graph contracts, plus explicitly optional official input.

The tiny XML fixtures are synthetic validator inputs, never official provenance.
Discovery always runs the pure contracts. Use --require-artifact for the dedicated
gate: a missing GQ778_ARTIFACT is then an error, not a successful skipped run.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / "quality_gameplay/gq778_attribute_visual_current69_20261123"
SPEC = importlib.util.spec_from_file_location("gq778_current71_contract", PACKAGE / "compose_current71.py")
compose = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compose)
ARTIFACT = os.environ.get("GQ778_ARTIFACT")


def item(parent, class_name, name, referent, source=None):
    node = ET.SubElement(parent, "Item", {"class": class_name, "referent": referent})
    props = ET.SubElement(node, "Properties")
    ET.SubElement(props, "string", {"name": "Name"}).text = name
    if source is not None:
        ET.SubElement(props, "string", {"name": "Source"}).text = source
    return node


def graph():
    """Six instances; two tiny sources; intentionally not an official69 fixture."""
    root = ET.Element("roblox", {"version": "4"})
    ET.SubElement(root, "External").text = "null"
    replicated = item(root, "ReplicatedStorage", "ReplicatedStorage", "r-storage")
    module = item(replicated, "ModuleScript", "OriginalModule", "r-module", "return 7\n")
    ET.SubElement(module.find("Properties"), "bool", {"name": "Archivable"}).text = "true"
    link = item(replicated, "ObjectValue", "OriginalLink", "r-link")
    ET.SubElement(link.find("Properties"), "Ref", {"name": "Value"}).text = "r-module"
    starter = item(root, "StarterPlayer", "StarterPlayer", "r-starter")
    scripts = item(starter, "StarterPlayerScripts", "StarterPlayerScripts", "r-scripts")
    item(scripts, "LocalScript", "OriginalClient", "r-client", "local untouched = true\n")
    return root


def xml(root):
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def by_name(root, name):
    matches = [node for node in root.iter("Item")
               if node.find("Properties/string[@name='Name']").text == name]
    if len(matches) != 1:
        raise AssertionError("fixture route is not unique: " + name)
    return matches[0]


def project():
    return {"tree": {
        "$className": "DataModel",
        "ReplicatedStorage": {"OriginalModule": {"$path": "sources/ReplicatedStorage/OriginalModule.luau"}},
        "StarterPlayer": {"StarterPlayerScripts": {
            "OriginalClient": {"$path": "sources/StarterPlayer/StarterPlayerScripts/OriginalClient.client.luau"}
        }},
    }}


class PureContracts(unittest.TestCase):
    def test_unique_json_and_nested_duplicates(self):
        self.assertEqual(compose.read_json(b'{"a":{"b":2}}'), {"a": {"b": 2}})
        for raw in (b'{"a":1,"a":2}', b'{"x":{"tree":1,"tree":2}}',
                    b'{"tree":{"Same":{},"Same":{}}}'):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
                compose.read_json(raw)

    def test_safe_relative_members(self):
        for path in ("sources/Module.luau", "a/b.client.luau", "folder/日本語.luau"):
            self.assertEqual(compose.safe_member(path), path)

    def test_unsafe_members_rejected(self):
        paths = ("", ".", "..", "../outside.luau", "/absolute.luau", "C:/absolute.luau",
                 "a/../b.luau", "a/./b.luau", "a//b.luau", "a/b/", "a\\b.luau",
                 "sources/evil\x00.luau", None, 1, {})
        for path in paths:
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "UNSAFE_ARTIFACT_PATH"):
                compose.safe_member(path)

    def test_project_inventory_exact_paths(self):
        self.assertEqual(compose.project_inventory(project()), {
            "ReplicatedStorage/OriginalModule": "sources/ReplicatedStorage/OriginalModule.luau",
            "StarterPlayer/StarterPlayerScripts/OriginalClient":
                "sources/StarterPlayer/StarterPlayerScripts/OriginalClient.client.luau",
        })

    def test_project_unsafe_and_non_source_paths(self):
        for path in ("../bad.luau", "/bad.luau", "sources/../bad.luau", "sources\\bad.luau",
                     "outside/good.luau", "sources/good.txt", "sources//good.luau"):
            value = project()
            value["tree"]["ReplicatedStorage"]["OriginalModule"]["$path"] = path
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "GQ778_RED_"):
                compose.project_inventory(value)

    def test_project_duplicate_source_path(self):
        value = project()
        value["tree"]["ReplicatedStorage"]["OtherRoute"] = {
            "$path": "sources/ReplicatedStorage/OriginalModule.luau"}
        with self.assertRaisesRegex(ValueError, "DUPLICATE_SOURCE_PATH"):
            compose.project_inventory(value)

    def test_project_invalid_nodes_routes_and_source_children(self):
        for name in ("", "bad/name", "bad\\name"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "PROJECT_ROUTE"):
                compose.project_inventory({"tree": {name: {"$path": "sources/a.luau"}}})
        with self.assertRaisesRegex(ValueError, "SOURCE_WITH_CHILDREN"):
            compose.project_inventory({"tree": {"A": {"$path": "sources/a.luau", "Child": {}}}})
        for value in ({}, {"tree": []}, []):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "PROJECT_TREE"):
                compose.project_inventory(value)
        with self.assertRaisesRegex(ValueError, "PROJECT_NODE"):
            compose.project_inventory({"tree": {"Bad": "value"}})

    def test_place_duplicate_routes_and_referents(self):
        original = graph()
        duplicate = copy.deepcopy(by_name(original, "OriginalModule"))
        duplicate.set("referent", "new-reference")
        by_name(original, "ReplicatedStorage").append(duplicate)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_INSTANCE_ROUTE"):
            compose.place_inventory(xml(original))
        original = graph()
        by_name(original, "OriginalClient").set("referent", "r-module")
        with self.assertRaisesRegex(ValueError, "PLACE_REFERENT"):
            compose.place_inventory(xml(original))

    def test_place_duplicate_source_or_name(self):
        for property_name in ("Source", "Name"):
            root = graph()
            props = by_name(root, "OriginalModule").find("Properties")
            props.append(copy.deepcopy(props.find("string[@name='" + property_name + "']")))
            with self.subTest(property_name=property_name), self.assertRaisesRegex(ValueError, "GQ778_RED_"):
                compose.place_inventory(xml(root))

    def test_source_xml_shape_is_preserved(self):
        for mutation in ("tag", "attribute", "child"):
            root = graph()
            source = by_name(root, "OriginalModule").find("Properties/string[@name='Source']")
            if mutation == "tag":
                source.tag = "ProtectedString"
            elif mutation == "attribute":
                source.set("unexpected", "true")
            else:
                ET.SubElement(source, "Unexpected").text = "hidden payload"
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "PLACE_SOURCE_PROPERTY_SHAPE"):
                compose.place_inventory(xml(root))

    def test_unexpected_instance_attributes_or_children(self):
        for mutation in ("attribute", "child", "source_on_folder", "two_properties"):
            root = graph()
            node = by_name(root, "ReplicatedStorage")
            if mutation == "attribute":
                node.set("extra", "value")
            elif mutation == "child":
                ET.SubElement(node, "Unexpected")
            elif mutation == "source_on_folder":
                ET.SubElement(node.find("Properties"), "string", {"name": "Source"}).text = "return 1"
            else:
                ET.SubElement(node, "Properties")
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "GQ778_RED_"):
                compose.place_inventory(xml(root))

    def test_xml_entities_and_root_format_rejected(self):
        for data in (b'<!DOCTYPE roblox [<!ENTITY x "bad">]><roblox version="4"/>',
                     b'<roblox version="3"/>', b'<roblox version="4" extra="x"/>', b'<other/>'):
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, "GQ778_RED_"):
                compose.place_inventory(data)

    def test_corrupt_zip_cannot_satisfy_real_lock(self):
        # The real lock is unchanged; no synthetic ZIP is accepted as provenance.
        lock = compose.read_json(compose.LOCK.read_bytes())
        with tempfile.TemporaryDirectory(prefix="gq778-corrupt-") as temporary:
            path = Path(temporary) / "bad.zip"
            path.write_bytes(b"not a ZIP archive")
            with self.assertRaisesRegex(ValueError, "OFFICIAL_ZIP_HASH"):
                compose.read_official_artifact(path, lock)

    def test_strict_entry_requires_artifact(self):
        environment = dict(os.environ)
        environment.pop("GQ778_ARTIFACT", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--require-artifact"],
                                capture_output=True, text=True, env=environment)
        self.assertEqual(result.returncode, 2)
        self.assertIn("GQ778_ARTIFACT_REQUIRED", result.stderr)

    def test_native_runner_preserves_foreign_existing_output(self):
        with tempfile.TemporaryDirectory(prefix="gq778-foreign-native-output-") as temporary:
            directory = Path(temporary)
            output = directory / "foreign-output"
            output.mkdir()
            (output / "FAILURE.json").write_bytes(b"FOREIGN_FAILURE_SENTINEL\n\x00preserve all bytes\n")
            (output / "foreign-subdir").mkdir()
            (output / "foreign-subdir/keep.bin").write_bytes(bytes(range(256)))

            def snapshot():
                return {
                    str(path.relative_to(output)): {
                        "device": path.lstat().st_dev,
                        "inode": path.lstat().st_ino,
                        "mode": path.lstat().st_mode,
                        "bytes": path.read_bytes() if path.is_file() else None,
                    }
                    for path in [output, *sorted(output.rglob("*"))]
                }

            before = snapshot()
            result = subprocess.run([
                sys.executable, "-B", str(PACKAGE / "native/run_current71.py"),
                "--out-dir", str(output),
                "--artifact", str(directory / "unused-artifact.zip"),
                "--luau-source", str(directory / "unused-luau-source"),
                "--rojo", str(directory / "unused-rojo"),
            ], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 1)
            self.assertIn("GQ778_RED_OUTPUT_ALREADY_EXISTS", result.stderr)
            self.assertEqual(snapshot(), before, "rejection may not alter any foreign member or inode")

    def test_native_runner_early_input_rejection_leaves_output_absent(self):
        with tempfile.TemporaryDirectory(prefix="gq778-unowned-native-output-") as temporary:
            directory = Path(temporary)
            output = directory / "unowned-new-output"
            artifact = directory / "invalid-artifact.zip"
            artifact.write_bytes(b"not the pinned official artifact")
            self.assertFalse(output.exists())
            result = subprocess.run([
                sys.executable, "-B", str(PACKAGE / "native/run_current71.py"),
                "--out-dir", str(output), "--artifact", str(artifact),
                "--luau-source", str(directory / "unused-luau-source"),
                "--rojo", str(directory / "unused-rojo"),
            ], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 1)
            self.assertIn("GQ778_RED_OFFICIAL_ZIP_HASH", result.stderr)
            self.assertNotIn("FRESH_LUAU_BUILD_START", result.stdout)
            self.assertFalse(output.exists(), "early failure may not claim an unowned output directory")
            self.assertFalse((output / "FAILURE.json").exists())


class OutputGraphPreservation(unittest.TestCase):
    def setUp(self):
        self.base = graph()
        self.items, self.envelope = compose.place_inventory(xml(self.base))
        self.bodies = {route: ("-- synthetic diagnostic body for " + route + "\n").encode()
                       for route in compose.ADDITIONS}

    def enabled_graph(self):
        root = copy.deepcopy(self.base)
        for index, (route, specification) in enumerate(compose.ADDITIONS.items()):
            parent_name, leaf = route.rsplit("/", 1)
            parent = by_name(root, parent_name.rsplit("/", 1)[-1])
            item(parent, specification["class_name"], leaf, "new-" + str(index), self.bodies[route].decode())
        return root

    def check(self, root, enabled=True):
        return compose.validate_output(xml(root), self.items, self.envelope, self.bodies, enabled)

    def test_valid_small_graph_on_off_and_referent_rebinding(self):
        self.assertEqual(len(self.check(self.enabled_graph())), len(self.items) + 2)
        self.assertEqual(self.check(self.base, enabled=False), self.items)
        remapped = self.enabled_graph()
        for node in remapped.iter("Item"):
            node.set("referent", "remapped-" + node.get("referent"))
        for reference in remapped.iter("Ref"):
            if reference.text == "r-module":
                reference.text = "remapped-r-module"
        self.assertEqual(len(self.check(remapped)), len(self.items) + 2)

    def test_existing_source_class_and_property_changes_rejected(self):
        for mutation in ("source", "class", "property_value", "property_added", "property_removed"):
            root = self.enabled_graph()
            node = by_name(root, "OriginalModule")
            props = node.find("Properties")
            if mutation == "source":
                props.find("string[@name='Source']").text += "-- changed\n"
            elif mutation == "class":
                node.set("class", "LocalScript")
            elif mutation == "property_value":
                props.find("bool[@name='Archivable']").text = "false"
            elif mutation == "property_added":
                ET.SubElement(props, "bool", {"name": "Disabled"}).text = "true"
            else:
                props.remove(props.find("bool[@name='Archivable']"))
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "OUTPUT_EXISTING_SOURCE_CLASS_OR_PROPERTY_DRIFT"):
                self.check(root)

    def test_addition_class_source_or_properties_rejected(self):
        for route in compose.ADDITIONS:
            for mutation in ("class", "source", "property"):
                root = self.enabled_graph()
                node = by_name(root, route.rsplit("/", 1)[-1])
                if mutation == "class":
                    node.set("class", "Script")
                elif mutation == "source":
                    node.find("Properties/string[@name='Source']").text += "-- wrong\n"
                else:
                    ET.SubElement(node.find("Properties"), "bool", {"name": "Disabled"}).text = "true"
                expected = "OUTPUT_ADDITION_PROPERTIES" if mutation == "property" else "OUTPUT_ADDITION_SOURCE_OR_CLASS"
                with self.subTest(route=route, mutation=mutation), self.assertRaisesRegex(ValueError, expected):
                    self.check(root)

    def test_source_transplant_between_same_class_instances_rejected(self):
        root = self.enabled_graph()
        original = by_name(root, "OriginalModule").find("Properties/string[@name='Source']")
        addition = by_name(root, "EGGRUMBLE_ElementVisuals").find("Properties/string[@name='Source']")
        original.text, addition.text = addition.text, original.text
        with self.assertRaisesRegex(ValueError, "OUTPUT_EXISTING_SOURCE_CLASS_OR_PROPERTY_DRIFT"):
            self.check(root)

    def test_extra_world_object_and_envelope_drift_rejected(self):
        for mutation in ("world_object", "envelope", "source_removed", "addition_removed"):
            root = self.enabled_graph()
            if mutation == "world_object":
                item(root, "Part", "UnexpectedWorldObject", "extra-world")
            elif mutation == "envelope":
                ET.SubElement(root, "External").text = "unexpected"
            elif mutation == "source_removed":
                by_name(root, "ReplicatedStorage").remove(by_name(root, "OriginalModule"))
            else:
                by_name(root, "ReplicatedStorage").remove(by_name(root, "EGGRUMBLE_ElementVisuals"))
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "OUTPUT_INSTANCE_OR_ENVELOPE_DRIFT"):
                self.check(root)

    def test_disabled_profile_rejects_additions(self):
        with self.assertRaisesRegex(ValueError, "OUTPUT_INSTANCE_OR_ENVELOPE_DRIFT"):
            self.check(self.enabled_graph(), enabled=False)

    def test_missing_source_property_cannot_be_ignored(self):
        root = self.enabled_graph()
        props = by_name(root, "OriginalModule").find("Properties")
        props.remove(props.find("string[@name='Source']"))
        with self.assertRaisesRegex(ValueError, "PLACE_SOURCE_PROPERTY"):
            self.check(root)


@unittest.skipUnless(ARTIFACT, "Explicit official-input checks require GQ778_ARTIFACT")
class ActualOfficialArtifact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = Path(ARTIFACT)
        (cls.lock, cls.project_bytes, cls.place_bytes, cls.sources,
         cls.project, cls.items, cls.envelope) = compose.read_official_artifact(cls.artifact)

    def test_exact_current69_input(self):
        self.assertEqual(self.lock["official_rc_sha"], "72d620d86761f2aa5da80263a251cc5fa63fecbb")
        self.assertEqual(len(self.sources), 69)
        self.assertEqual(len(self.items), 75)
        self.assertEqual(len(compose.project_inventory(self.project)), 69)
        self.assertFalse(set(compose.ADDITIONS) & set(self.items))
        self.assertEqual(compose.digest(self.artifact.read_bytes()), self.lock["artifact"]["sha256"])

    def test_actual_source_mutation_rejected(self):
        changed = dict(self.sources)
        first = sorted(changed)[0]
        changed[first] += b"\n-- injected source drift\n"
        with self.assertRaisesRegex(ValueError, "OFFICIAL_SOURCE_HASH_OR_ROUTE"):
            compose.validate_official(self.project_bytes, self.place_bytes, changed, self.lock)

    def test_actual_missing_or_additional_source_rejected(self):
        for mutation in ("missing", "additional"):
            changed = dict(self.sources)
            if mutation == "missing":
                changed.pop(next(iter(changed)))
            else:
                changed["sources/ServerScriptService/Unexpected.luau"] = b"return 1\n"
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "OFFICIAL_SOURCE_PATH_SET"):
                compose.validate_official(self.project_bytes, self.place_bytes, changed, self.lock)

    def test_actual_zip_truncation_and_byte_corruption_rejected(self):
        raw = self.artifact.read_bytes()
        corrupt = bytearray(raw)
        corrupt[len(corrupt) // 2] ^= 1
        with tempfile.TemporaryDirectory(prefix="gq778-actual-negative-") as temporary:
            for name, data in (("truncated.zip", raw[:-16]), ("corrupt.zip", bytes(corrupt))):
                path = Path(temporary) / name
                path.write_bytes(data)
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "OFFICIAL_ZIP_HASH"):
                    compose.read_official_artifact(path)

    def test_actual_off69_graph_identity(self):
        self.assertEqual(compose.validate_output(self.place_bytes, self.items, self.envelope, {}, False), self.items)

    def test_concurrent_empty_destination_is_preserved_at_publication(self):
        # Only the external Rojo process is modeled. The input ZIP, lock, staged
        # 69 sources and resulting OFF XML are the genuine pinned input bytes.
        with tempfile.TemporaryDirectory(prefix="gq778-destination-race-") as temporary:
            destination = Path(temporary) / "foreign-output"
            observed = []
            foreign_identity = []

            def mocked_rojo(argv, **kwargs):
                self.assertEqual(kwargs, {"check": True, "text": True, "capture_output": True})
                self.assertFalse(destination.exists(), "foreign directory must appear after initial guard")
                observed.append(argv[1])
                if argv[1:] == ["--version"]:
                    return subprocess.CompletedProcess(argv, 0, self.lock["rojo_version"] + "\n", "")
                self.assertEqual(argv[1], "build")
                self.assertEqual(len(argv), 5)
                self.assertEqual(argv[3], "-o")
                project_path, place_path = Path(argv[2]), Path(argv[4])
                self.assertEqual(project_path.read_bytes(), self.project_bytes)
                self.assertEqual(project_path.parent, place_path.parent)
                for relative, body in self.sources.items():
                    self.assertEqual((project_path.parent / relative).read_bytes(), body)
                place_path.write_bytes(self.place_bytes)
                # Another producer creates an EMPTY directory during the build.
                # os.replace(stage, destination) could silently overwrite this.
                destination.mkdir()
                foreign_identity.append((destination.stat().st_dev, destination.stat().st_ino))
                return subprocess.CompletedProcess(argv, 0, "modeled exact OFF69 build\n", "")

            with patch.object(compose.subprocess, "run", side_effect=mocked_rojo):
                with self.assertRaises(FileExistsError):
                    compose.compose(self.artifact, destination, Path("unused-modeled-rojo"), enabled=False)
            self.assertEqual(observed, ["--version", "build"])
            self.assertEqual(len(foreign_identity), 1)
            self.assertTrue(destination.is_dir())
            self.assertEqual((destination.stat().st_dev, destination.stat().st_ino), foreign_identity[0])
            self.assertEqual(list(destination.iterdir()), [], "foreign empty directory must remain empty")
            self.assertFalse((destination / "COMPOSITION_RECEIPT.json").exists())

    def test_source_changed_during_external_build_is_not_published(self):
        with tempfile.TemporaryDirectory(prefix="gq778-source-race-") as temporary:
            destination = Path(temporary) / "must-not-publish"
            observed = []
            first_source = sorted(self.sources)[0]

            def mocked_rojo(argv, **kwargs):
                self.assertEqual(kwargs, {"check": True, "text": True, "capture_output": True})
                self.assertFalse(destination.exists())
                observed.append(argv[1])
                if argv[1:] == ["--version"]:
                    return subprocess.CompletedProcess(argv, 0, self.lock["rojo_version"] + "\n", "")
                self.assertEqual(argv[1], "build")
                self.assertEqual(len(argv), 5)
                self.assertEqual(argv[3], "-o")
                project_path, place_path = Path(argv[2]), Path(argv[4])
                self.assertEqual(project_path.read_bytes(), self.project_bytes)
                # The already-built Place is still entirely genuine. Mutate only
                # the staged source afterwards to exercise post-build retention.
                place_path.write_bytes(self.place_bytes)
                source_path = project_path.parent / first_source
                self.assertEqual(source_path.read_bytes(), self.sources[first_source])
                source_path.write_bytes(self.sources[first_source] + b"\n-- late external mutation\n")
                return subprocess.CompletedProcess(argv, 0, "modeled exact OFF69 build before source drift\n", "")

            with patch.object(compose.subprocess, "run", side_effect=mocked_rojo):
                with self.assertRaisesRegex(ValueError, "OUTPUT_SOURCE_CHANGED_DURING_BUILD"):
                    compose.compose(self.artifact, destination, Path("unused-modeled-rojo"), enabled=False)
            self.assertEqual(observed, ["--version", "build"])
            self.assertFalse(destination.exists(), "source drift must fail before destination publication")
            self.assertFalse((destination / "COMPOSITION_RECEIPT.json").exists())


if __name__ == "__main__":
    if "--require-artifact" in sys.argv:
        sys.argv.remove("--require-artifact")
        if not ARTIFACT or not ARTIFACT.strip() or not Path(ARTIFACT).is_file():
            print("GQ778_ARTIFACT_REQUIRED: provide the exact official ZIP for the dedicated gate", file=sys.stderr)
            raise SystemExit(2)
    unittest.main()
