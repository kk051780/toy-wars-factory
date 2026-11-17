#!/usr/bin/env python3
"""Independent negative and positive receipts for real31 V3 source hydration."""
from pathlib import Path
import hashlib
import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("rehydrate_real31",HERE/"rehydrate_real31.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
HEAD="a"*40
KINDS=["Script","ModuleScript","LocalScript"]


def fixture(root):
    data={"name":"V3_TEST","tree":{"$className":"DataModel",
        "ServerScriptService":{"$className":"ServerScriptService"}}}
    top=ET.Element("roblox",{"version":"4"})
    srv=ET.SubElement(top,"Item",{"class":"ServerScriptService","referent":"0"})
    name=ET.SubElement(ET.SubElement(srv,"Properties"),"string",{"name":"Name"})
    name.text="ServerScriptService"
    source_names=[
        "EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_SwarmCombat",
        "EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_FlagshipFieldArt",
        "EGGRUMBLE_CastleMatchRules","EGGRUMBLE_FieldItemPickups",
        "EGGRUMBLE_ScoreBalance","EGGRUMBLE_CombatBalance",
    ]+["Sample_"+str(n) for n in range(23)]
    assert len(source_names)==31
    for i,name in enumerate(source_names):
        cls=KINDS[i%len(KINDS)]
        ext=m.CLASSES[cls]
        data["tree"]["ServerScriptService"][name]={"$path":"none/"+name+ext}
        item=ET.SubElement(srv,"Item",{"class":cls,"referent":str(i+1)})
        props=ET.SubElement(item,"Properties")
        ET.SubElement(props,"string",{"name":"Name"}).text=name
        ET.SubElement(props,"string",{"name":"Source"}).text="-- Lua script "+name+"\nreturn 1\n"
    place=root/"official.rbxlx"
    ET.ElementTree(top).write(place,encoding="utf-8",xml_declaration=True)
    template=root/"CURRENT31.project.json"
    template.write_text(json.dumps(data))
    receipt=root/"official.json"
    receipt.write_text(json.dumps({"github_commit_sha":HEAD,
        "official_rc_commit_verified":True,"place_sha256":m.sha(place)}))
    return place,template,receipt


class HydrateTests(unittest.TestCase):
    def test_real31_extract_one_route_each(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            place,template,receipt=fixture(root)
            out=root/"export"
            project=m.extract(place,template,receipt,out,HEAD)
            assert project.is_file()
            model=json.loads(project.read_text())
            assert len(m.flat_project(model))==31
            for rel,node in m.flat_project(model).items():
                f=(project.parent/node["$path"]).resolve()
                self.assertTrue(f.exists())
                self.assertTrue(f.read_text().startswith("-- Lua script "))
            self.assertEqual(len(m.tree_scripts(ET.parse(place).getroot())),31)

    def test_reject_receipt_head_or_place_drift(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            place,template,receipt=fixture(root)
            with self.assertRaisesRegex(ValueError,"RED_NOT_ACTUAL_SAMEHEAD"):
                m.extract(place,template,receipt,root/"export",HEAD.replace("a","b"))
            x=json.loads(receipt.read_text())
            x["place_sha256"]="0"*64;receipt.write_text(json.dumps(x))
            with self.assertRaisesRegex(ValueError,"RED_OFFICIAL_PLACE_SHA"):
                m.extract(place,template,receipt,root/"export",HEAD)

    def test_reject_missing_source_on_real_place(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            place,template,receipt=fixture(root)
            model=json.loads(template.read_text())
            del model["tree"]["ServerScriptService"]["Sample_22"]
            template.write_text(json.dumps(model))
            with self.assertRaisesRegex(ValueError,"RED_NOT_CANONICAL31"):
                m.extract(place,template,receipt,root/"export",HEAD)

    def test_verify_true_rojo_source_and_negative_mutant(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            place,template,receipt=fixture(root)
            project=m.extract(place,template,receipt,root/"export",HEAD)
            m.verify_built(project,place,31)
            fake=ET.parse(place)
            s=fake.getroot().find(".//Item[@class='Script']/Properties/string[@name='Source']")
            self.assertIsNotNone(s)
            s.text+="--evil-mutant"
            mutant=root/"mutant.rbxlx"
            fake.write(mutant,encoding="utf-8",xml_declaration=True)
            with self.assertRaisesRegex(ValueError,"RED_REAL_ROJO_SOURCE"):
                m.verify_built(project,mutant,31)


if __name__=="__main__":
    unittest.main()
