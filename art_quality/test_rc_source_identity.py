#!/usr/bin/env python3
"""Execute positive/negative source-to-instance binding tests, not text greps."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from verify_rc_source_identity import verify, expected_bindings, blob

SCRIPTS = {
    "server/Game.server.luau": "local GAME_AUTHORITY=1\n",
    "server/Horde.luau": "local HORDE_MOBS=9\n",
    "client/HUD.client.luau": "local TOUCH_ATTACK=1\n",
    "client/Foliage.client.luau": "local LEAVES_VISIBLE=true\n",
}
GAME = ("ServerScriptService/TrapRaidersS1/Game", "Script")
HORDE = ("ServerScriptService/TrapRaidersS1/Horde", "ModuleScript")
HUD = ("StarterPlayer/StarterPlayerScripts/TrapRaidersHUD", "LocalScript")
FOLIAGE = ("StarterPlayer/StarterPlayerScripts/Foliage", "LocalScript")


def item(parent, kind, name, source=None):
    el = ET.SubElement(parent, "Item", {"class": kind})
    props = ET.SubElement(el, "Properties")
    ET.SubElement(props, "string", {"name": "Name"}).text = name
    if source is not None:
        ET.SubElement(props, "string", {"name": "Source"}).text = source
    return el


class SourceIdentityGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dist = self.root / "dist"
        self.place = self.root / "place.rbxlx"
        self.report = self.root / "receipt.json"
        for name, text in SCRIPTS.items():
            p = self.dist / "src" / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, "utf8")
        paths = self.dist / "src"
        src = {
            p.relative_to(paths).as_posix(): p.read_bytes()
            for p in sorted(paths.rglob("*.luau"))
        }
        pins = {name: blob(data) for name, data in src.items()}
        (self.dist / "SOURCE_LOCK.json").write_text(
            json.dumps({"total_scripts": len(src), "blobs": pins}), "utf8"
        )
        (self.dist / "RC_FEATURE_LOCK.json").write_text(
            json.dumps({"total_sources": len(src), "source_gitblobs": pins}), "utf8"
        )
        project = {
            "name": "P0D_QA_SYNTHETIC",
            "tree": {
                "$className": "DataModel",
                "ServerScriptService": {
                    "$className": "ServerScriptService",
                    "TrapRaidersS1": {"$path": "src/server"},
                },
                "StarterPlayer": {
                    "$className": "StarterPlayer",
                    "StarterPlayerScripts": {
                        "$className": "StarterPlayerScripts",
                        "TrapRaidersHUD": {"$path": "src/client/HUD.client.luau"},
                        "Foliage": {"$path": "src/client/Foliage.client.luau"},
                    },
                },
            },
        }
        (self.dist / "default.project.json").write_text(json.dumps(project), "utf8")
        self.reset_xml()

    def tearDown(self):
        self.temp.cleanup()

    def reset_xml(self):
        self.xml = ET.Element("roblox", {"version": "4"})
        server = item(self.xml, "ServerScriptService", "ServerScriptService")
        server_root = item(server, "Folder", "TrapRaidersS1")
        self.script_items = {
            GAME: item(server_root, "Script", "Game", SCRIPTS["server/Game.server.luau"]),
            HORDE: item(server_root, "ModuleScript", "Horde", SCRIPTS["server/Horde.luau"]),
        }
        starter = item(self.xml, "StarterPlayer", "StarterPlayer")
        scripts = item(starter, "StarterPlayerScripts", "StarterPlayerScripts")
        self.script_items[HUD] = item(
            scripts, "LocalScript", "TrapRaidersHUD", SCRIPTS["client/HUD.client.luau"]
        )
        self.script_items[FOLIAGE] = item(
            scripts, "LocalScript", "Foliage", SCRIPTS["client/Foliage.client.luau"]
        )
        self.save()

    def save(self):
        self.place.write_bytes(ET.tostring(self.xml, encoding="utf8"))

    def test_exact_four_scripts_and_hud_alias(self):
        expected = expected_bindings(self.dist)
        self.assertEqual(set(expected), {GAME, HORDE, HUD, FOLIAGE})
        report = verify(self.dist, self.place, self.report, 4)
        self.assertEqual(report["embedded_count"], 4)
        self.assertTrue(report["all_instance_class_name_path_source_exact"])

    def test_rojo_protected_string_source_is_accepted(self):
        node = self.script_items[GAME].find("Properties/string[@name='Source']")
        node.tag = "ProtectedString"
        self.save()
        result = verify(self.dist, self.place, self.report, 4)
        self.assertEqual(result["source_count"], 4)

    def test_root_datamodel_item_does_not_change_instance_paths(self):
        wrapped = ET.Element("roblox", {"version": "4"})
        root_game = item(wrapped, "DataModel", "Game")
        for child in list(self.xml):
            self.xml.remove(child)
            root_game.append(child)
        self.xml = wrapped
        self.save()
        result = verify(self.dist, self.place, self.report, 4)
        self.assertEqual(result["embedded_count"], 4)

    def test_python_optimized_mode_cannot_emit_false_pass(self):
        cmd = [
            sys.executable, "-O",
            str(Path(__file__).with_name("verify_rc_source_identity.py")),
            "--dist", str(self.dist),
            "--place", str(self.place),
            "--receipt", str(self.report), "--count", "4"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0, "Python -O must be rejected")
        self.assertIn("P0D_IDENTITY_GATE_PYTHON_OPTIMIZATION_FORBIDDEN", result.stderr)
        self.assertFalse(self.report.exists())

    def test_wrong_source_on_correct_script_rejected(self):
        el = self.script_items[GAME].find("Properties/string[@name='Source']")
        el.text = "local MALICIOUS_GAME=1\n"
        self.save()
        with self.assertRaisesRegex(AssertionError, "SOURCE_WRONG_INSTANCE"):
            verify(self.dist, self.place, self.report, 4)
        self.assertFalse(self.report.exists())

    def test_swapped_equal_source_multiset_rejected(self):
        a = self.script_items[GAME].find("Properties/string[@name='Source']")
        b = self.script_items[HORDE].find("Properties/string[@name='Source']")
        a.text, b.text = b.text, a.text
        # Old Counter(source strings) cannot detect this; full identity check must.
        self.assertEqual(
            sorted([a.text, b.text]),
            sorted([SCRIPTS["server/Game.server.luau"], SCRIPTS["server/Horde.luau"]]),
        )
        self.save()
        with self.assertRaisesRegex(AssertionError, "SOURCE_WRONG_INSTANCE"):
            verify(self.dist, self.place, self.report, 4)

    def test_script_without_source_rejected(self):
        self.script_items[HUD].find("Properties").remove(
            self.script_items[HUD].find("Properties/string[@name='Source']")
        )
        self.save()
        with self.assertRaisesRegex(AssertionError, "SCRIPT_WITHOUT_SOURCE"):
            verify(self.dist, self.place, self.report, 4)

    def test_extra_source_less_script_rejected(self):
        folder = self.script_items[GAME]
        extra = item(folder, "LocalScript", "HiddenSourceLess")
        self.save()
        with self.assertRaisesRegex(AssertionError, "SCRIPT_WITHOUT_SOURCE"):
            verify(self.dist, self.place, self.report, 4)

    def test_wrong_instance_path_rejected(self):
        name = self.script_items[HUD].find("Properties/string[@name='Name']")
        name.text = "NotTrapRaidersHUD"
        self.save()
        with self.assertRaisesRegex(AssertionError, "INSTANCE_PATH_OR_CLASS_DRIFT"):
            verify(self.dist, self.place, self.report, 4)

    def test_wrong_ancestor_service_class_rejected(self):
        service = self.xml.find("Item[@class='ServerScriptService']")
        self.assertIsNotNone(service)
        service.set("class", "Folder")  # same name & all Luau unchanged
        self.save()
        with self.assertRaisesRegex(AssertionError, "ROJO_ANCESTOR_CLASS_DRIFT"):
            verify(self.dist, self.place, self.report, 4)
        self.assertFalse(self.report.exists())

    def test_slash_instance_name_spoof_rejected(self):
        node = self.script_items[HUD].find("Properties/string[@name='Name']")
        node.text = "Escaped/TrapRaidersHUD"
        self.save()
        with self.assertRaisesRegex(AssertionError, "INVALID_INSTANCE_NAME"):
            verify(self.dist, self.place, self.report, 4)

    def test_wrong_script_class_rejected(self):
        self.script_items[GAME].set("class", "ModuleScript")
        self.save()
        with self.assertRaisesRegex(AssertionError, "INSTANCE_PATH_OR_CLASS_DRIFT"):
            verify(self.dist, self.place, self.report, 4)

    def test_corrupted_git_blob_lock_rejected(self):
        p = self.dist / "SOURCE_LOCK.json"
        obj = json.loads(p.read_text())
        obj["blobs"]["server/Game.server.luau"] = "0" * 40
        p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(AssertionError, "SOURCE_BLOB_LOCK_DRIFT"):
            verify(self.dist, self.place, self.report, 4)

    def test_unknown_explicit_project_mapping_rejected(self):
        p = self.dist / "default.project.json"
        obj = json.loads(p.read_text())
        obj["tree"]["StarterPlayer"]["StarterPlayerScripts"]["Missing"] = {
            "$path": "src/client/NotFound.client.luau"
        }
        p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(AssertionError, "MISSING_LUAU_SOURCE"):
            verify(self.dist, self.place, self.report, 4)

    def test_untrusted_xml_entity_rejected(self):
        self.place.write_bytes(b'<!DOCTYPE r [<!ENTITY boom "bad">]><roblox/>')
        with self.assertRaisesRegex(AssertionError, "XML_ENTITY_REJECTED"):
            verify(self.dist, self.place, self.report, 4)


if __name__ == "__main__":
    unittest.main()
