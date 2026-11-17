"""Synthetic edge regressions for composer; real exact31 is separately rebuilt in CI."""
import json
import tempfile
import unittest
from pathlib import Path

from compose_element32 import compose, inventory


class ElementComposerTests(unittest.TestCase):
    def fixture(self, root: Path):
        source = root/"source"
        source.mkdir()
        server={"$className":"ServerScriptService"}
        for i, name in enumerate(
            ["EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_SwarmCombat"] +
            [f"TEST_CANONICAL_{n:02d}" for n in range(29)]
        ):
            f=source/(name+".server.luau")
            f.write_text(f"-- unique original #{i}\nprint('{name}')\n","utf-8")
            server[name]={"$path":f.name}
        project=source/"ORIGINAL31.project.json"
        project.write_text(json.dumps({"name":"ORIGINAL31","tree":{"$className":"DataModel","ServerScriptService":server}}),"utf-8")
        return project

    def test_real_byte_only_on_off(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            old=self.fixture(root)
            enabled=root/"result"/"ON32.project.json"
            disabled=root/"result"/"OFF31.project.json"
            r=compose(old,enabled,True)
            off=compose(old,disabled,False)
            self.assertEqual((r["source_count"],off["source_count"]),(32,31))
            _, files=inventory(enabled)
            self.assertEqual(len(files),32)
            self.assertIn(("ReplicatedStorage","EGGRUMBLE_ElementAffinityPolicy"),files)
            self.assertTrue(r["original31_exact"] and off["original31_exact"])
            self.assertEqual(set(inventory(old)[1]),set(inventory(disabled)[1]))

    def test_refuses_wrong_script_count(self):
        with tempfile.TemporaryDirectory() as t:
            old=self.fixture(Path(t))
            data=json.loads(old.read_text())
            del data["tree"]["ServerScriptService"]["TEST_CANONICAL_00"]
            old.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"RED_SOURCE_IS_NOT_CANONICAL31"):
                compose(old,Path(t)/"wrong.project.json",True)

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);old=self.fixture(root)
            with self.assertRaisesRegex(ValueError,"RED_REFUSE_OVERWRITE"):
                compose(old,old,True)


if __name__=="__main__":
    unittest.main()
