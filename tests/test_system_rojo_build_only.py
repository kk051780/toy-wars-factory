"""Rojo build-only bridge: test-first source, event, binary framing, and workflow guards.

These fixtures do NOT prove actual Roblox engine execution or publishing.
"""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import rojo_source_contract as sc
from tools import rojo_rbxl_gate as gate

WF = ROOT / ".github/workflows/toy-wars-rojo-build-only.yml"

def fake_rbxl(types=("INST", "PROP", "PRNT", "END")):
    header = gate.MAGIC + struct.pack("<HIIQ", 0, 3, 5, 0)
    chunks = b""
    for kind in types:
        payload = b"</roblox>" if kind == "END" else b"fixture"
        chunks += struct.pack("<4sIII", kind.encode().ljust(4, b"\0"), 0, len(payload), 0) + payload
    return header + chunks

class SourceContractTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.pins = {}
        for name in sc.PINS:
            file = self.root / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("test source: " + name, encoding="utf-8")
            self.pins[name] = sc.git_blob_sha(file.read_bytes())
        (self.root / "default.project.json").write_text(json.dumps(sc.EXPECTED_PROJECT))

    def test_source_mapping_exact(self):
        self.assertEqual(sc.check_sources(self.root, self.pins), self.pins)
        self.assertEqual(sc.validate_project(self.root), sc.EXPECTED_PROJECT)

    def test_modified_source_rejected(self):
        path = self.root / next(iter(self.pins))
        path.write_text("mutated")
        with self.assertRaises(ValueError):
            sc.check_sources(self.root, self.pins)

    def test_missing_source_rejected(self):
        (self.root / next(iter(self.pins))).unlink()
        with self.assertRaises(ValueError):
            sc.check_sources(self.root, self.pins)

    def test_symlinked_source_rejected(self):
        path = self.root / next(iter(self.pins))
        path.unlink()
        target = self.root / "another-file"
        target.write_text("test source")
        path.symlink_to(target)
        with self.assertRaises(ValueError):
            sc.check_sources(self.root, self.pins)

    def test_modified_project_mapping_rejected(self):
        p = self.root / "default.project.json"
        bad = json.loads(p.read_text())
        bad["tree"]["ReplicatedStorage"]["AnotherRemote"] = {"$className": "RemoteEvent"}
        p.write_text(json.dumps(bad))
        with self.assertRaises(ValueError):
            sc.validate_project(self.root)

    def test_duplicate_project_json_key_rejected(self):
        (self.root / "default.project.json").write_text('{"name":"A","name":"B","tree":{}}')
        with self.assertRaises(ValueError):
            sc.validate_project(self.root)

    def test_expected_source_blob_pins_are_full_git_hashes(self):
        self.assertEqual(len(sc.PINS), 4)
        self.assertTrue(all(len(value) == 40 for value in sc.PINS.values()))
        self.assertEqual(sc.PINS["src/ToyWarsHUD.client.lua"], "f1b7a2e2e4e6cd0a5703a7f034f50d4e62801467")

    def test_correct_manual_main_event_only(self):
        env = dict(GITHUB_REPOSITORY="kk051780/toy-wars-factory",
                   GITHUB_REF="refs/heads/main", GITHUB_EVENT_NAME="workflow_dispatch",
                   GITHUB_SHA="a" * 40)
        self.assertEqual(sc.check_event(env), "a" * 40)
        for key,value in (("GITHUB_REPOSITORY","other/repo"),("GITHUB_REF","refs/heads/feature"),
                          ("GITHUB_EVENT_NAME","pull_request"),("GITHUB_SHA","bad")):
            e = dict(env, **{key:value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                sc.check_event(e)

    def test_real_temp_git_post_merge_ancestor(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        for key,value in [("user.email","ci@example.invalid"),("user.name","Fixture")]:
            subprocess.run(["git", "-C", str(self.root), "config", key, value], check=True)
        subprocess.run(["git","-C",str(self.root),"add","."],check=True)
        subprocess.run(["git","-C",str(self.root),"commit","-qm","source baseline"],check=True)
        base=subprocess.check_output(["git","-C",str(self.root),"rev-parse","HEAD"],text=True).strip()
        (self.root/"workflow-added").write_text("new metadata")
        subprocess.run(["git","-C",str(self.root),"add","."],check=True)
        subprocess.run(["git","-C",str(self.root),"commit","-qm","workflow addition"],check=True)
        head=subprocess.check_output(["git","-C",str(self.root),"rev-parse","HEAD"],text=True).strip()
        env=dict(GITHUB_REPOSITORY="kk051780/toy-wars-factory",GITHUB_REF="refs/heads/main",
                 GITHUB_EVENT_NAME="workflow_dispatch",GITHUB_SHA=head)
        self.assertEqual(sc.check_checkout(self.root,env,baseline=base,pins=self.pins),head)
        with self.assertRaises(ValueError):
            sc.check_checkout(self.root,dict(env,GITHUB_SHA=base),baseline=base,pins=self.pins)
        with self.assertRaises(ValueError):
            sc.check_checkout(self.root,env,baseline="f"*40,pins=self.pins)

class BinaryGateTests(unittest.TestCase):
    def test_framed_file_is_only_static_build_receipt(self):
        d=gate.inspect(fake_rbxl())
        self.assertEqual(set(d["chunk_types"]), {"INST","PROP","PRNT","END"})
        self.assertFalse(d["engine_verified"])
        self.assertFalse(d["published"])

    def test_corrupt_magic_rejected(self):
        with self.assertRaises(ValueError):
            gate.inspect(b"invalid"+fake_rbxl())

    def test_truncated_chunk_rejected(self):
        with self.assertRaises(ValueError):
            gate.inspect(fake_rbxl()[:-2])

    def test_missing_end_rejected(self):
        with self.assertRaises(ValueError):
            gate.inspect(fake_rbxl(("INST","PROP","PRNT")))

    def test_missing_instance_chunks_rejected(self):
        with self.assertRaises(ValueError):
            gate.inspect(fake_rbxl(("INST","END")))

    def test_trailing_bytes_rejected(self):
        with self.assertRaises(ValueError):
            gate.inspect(fake_rbxl()+b"later")

    def test_duplicate_end_rejected(self):
        with self.assertRaises(ValueError):
            gate.inspect(fake_rbxl(("INST","PROP","PRNT","END","END")))

    def test_oversized_binary_rejected(self):
        with self.assertRaises(ValueError):
            gate.inspect(fake_rbxl()+b"x"*(10*1024*1024))

class WorkflowPolicyTests(unittest.TestCase):
    def test_manual_only_and_read_only(self):
        y=WF.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:",y)
        self.assertNotIn("pull_request:",y)
        self.assertNotIn("\n  push:",y)
        self.assertIn("contents: read",y)
        self.assertIn("persist-credentials: false",y)
        self.assertIn("fetch-depth: 0",y)

    def test_no_secrets_or_publish_commands(self):
        y=WF.read_text(encoding="utf-8").lower()
        for forbidden in ("secrets.","rojo upload","roblox publish",
                          "studio publish","open-cloud","api.roblox.com",
                          "permissions: write-all","pull_request_target"):
            with self.subTest(text=forbidden):
                self.assertNotIn(forbidden,y)

    def test_pinned_tool_and_artifact_gate(self):
        y=WF.read_text(encoding="utf-8")
        self.assertIn("paradoxum-games/setup-rokit@29e6ee09651a3711e3a287a1037671d7b74db6d0",y)
        self.assertIn("actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",y)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",y)
        self.assertIn("rojo_source_contract.py",y)
        self.assertIn("rojo_rbxl_gate.py",y)
        self.assertIn("rojo build",y)

if __name__=="__main__":
    unittest.main()
