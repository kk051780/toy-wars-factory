#!/usr/bin/env python3
"""Nonduplication and exact inverse tests for existing Swarm fan overlay."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("overlay_squad",HERE/"overlay_squad.py")
assert spec and spec.loader
fan=importlib.util.module_from_spec(spec);spec.loader.exec_module(fan)

class RealNeutralSquadFanTest(unittest.TestCase):
    @staticmethod
    def source():
        return fan.HELPER_ANCHOR+fan.OLD+" -- neutralSpawnClear(point)\n -- GetPartBoundsInBox\n"

    def test_exact_inverse_swarm_only(self):
        old=self.source();new=fan.patch(old)
        self.assertEqual(fan.unpatch(new),old)
        self.assertEqual(new.count("EncounterFair.chooseIndex(encounterFairState,session,kinds)"),1)
        self.assertEqual(new.count("local fanGroup=math.min(batch,5)"),1)
        self.assertEqual(new.count("addEnemy(Vector3.new(at.X,session.groundY or target.Y-4,at.Z))"),1)
        self.assertIn("local d=math.random(38,48)",new)
        self.assertIn("local squadBearing=math.random()*math.pi*2",new)
        for forbidden in ["Instance.new(", "TakeDamage(", "SetAttribute(", "DataStore", "RemoteEvent", "LastAttackerId"]:
            self.assertNotIn(forbidden,fan.NEW+fan.HELPER)

    def test_drift_duplicate_collision_gate_rejected(self):
        source=self.source()
        for wrong in (source.replace(fan.OLD,""),source.replace(fan.OLD,fan.OLD*2),
                      source.replace("GetPartBoundsInBox",""),source.replace("neutralSpawnClear(point)","")):
            with self.subTest(wrong=wrong[:35]):
                with self.assertRaisesRegex(ValueError,"RED_"):
                    fan.patch(wrong)
        with self.assertRaisesRegex(ValueError,"RED_"):
            fan.patch(fan.patch(source))

    def test_selected_swarm_and_off31_preserve_other30(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/"source";source.mkdir()
            server={"$className":"ServerScriptService"}
            for i in range(31):
                name="EGGRUMBLE_SwarmCombat" if i==0 else "EGGRUMBLE_LobbyCastleModesPreview" if i==1 else "CANONICAL_"+str(i)
                p=source/(name+".luau")
                p.write_text(self.source() if i==0 else "return {}\n")
                server[name]={"$path":"source/"+p.name}
            project={"name":"SWARM_ONLY_TEST","tree":{"$className":"DataModel","ServerScriptService":server}}
            base=root/"base31.project.json";base.write_text(json.dumps(project))
            out=root/"selected"/"on31.project.json"
            receipt=fan.compose(base,out)
            self.assertEqual(receipt["selected_source_count"],31)
            self.assertTrue(receipt["other30_byte_exact"])
            self.assertEqual(receipt["actual_added_soldiers"],0)
            before,original=fan.m.flat(base)
            after,selected=fan.m.flat(out)
            self.assertEqual(set(original),set(selected))
            for key,p in original.items():
                if key[-1]=="EGGRUMBLE_SwarmCombat":
                    self.assertEqual(fan.unpatch(selected[key].read_text()),p.read_text())
                else:
                    self.assertEqual(selected[key].read_bytes(),p.read_bytes())
            self.assertNotEqual(before["name"],after["name"])
            with self.assertRaisesRegex(ValueError,"RED_EXISTING_OUTPUT"):
                fan.compose(base,out)

if __name__=="__main__":
    unittest.main()
