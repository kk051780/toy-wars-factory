#!/usr/bin/env python3
"""Synthetic negative tests for the exact 31-route GQ611 adaptor (NOT Studio evidence)."""
from __future__ import annotations
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest import TestCase,main,mock
import xml.etree.ElementTree as ET

spec=importlib.util.spec_from_file_location("gq611_select",Path(__file__).with_name("select_guard.py"))
assert spec and spec.loader
gq=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gq)

OLD=b'--!strict\nlocal MAX_DISTANCE=16\nreturn Guard\n'
NEW=(
 b'--!strict\nlocal MAX_DISTANCE=16\n'
 b'local function configuredReach(part:BasePart,verb:string):number?\n'
 b'if selected then return nil end\n'
 b'if (near-root.Position).Magnitude>reach+EXCESS_RADIUS then return false end\n'
 b'if not positionValid(actor,part,verb) then return false end\n'
 b'return Guard\n'
)

def fixture(base_dir:Path):
    base_dir.mkdir(parents=True,exist_ok=True)
    orig=base_dir/"author482.luau"
    chosen=base_dir/"author611.luau"
    orig.write_bytes(OLD)
    chosen.write_bytes(NEW)
    branches={"ServerScriptService":{"EGGRUMBLE_InteractionGuard":{"$path":"Guard.luau"}}}
    (base_dir/"Guard.luau").write_bytes(OLD)
    for i in range(30):
        name="OTHER_%02d"%i
        path=name+".luau"
        (base_dir/path).write_text("return {}\n",encoding="utf-8")
        branches["ServerScriptService"][name]={"$path":path}
    project=base_dir/"CURRENT31.project.json"
    project.write_text(json.dumps({"name":"test","tree":branches}))
    return project,orig,chosen,base_dir/"GQ611_FINAL31.project.json"

def make_place(project:Path,out:Path):
    _,mapping=gq.scan(project)
    root=ET.Element("roblox",version="4")
    for route,path in mapping.items():
        item=ET.SubElement(root,"Item",{"class":"ModuleScript"})
        props=ET.SubElement(item,"Properties")
        ET.SubElement(props,"string",name="Name").text=route[-1]
        ET.SubElement(props,"ProtectedString",name="Source").text=path.read_text()
    out.write_bytes(ET.tostring(root,encoding="utf-8"))

class Adapter(TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.base,self.orig,self.selected,self.out=fixture(self.root)
        p1=mock.patch.object(gq,"ORIGINAL_BLOB",gq.gitblob(OLD))
        p2=mock.patch.object(gq,"SELECTED_BLOB",gq.gitblob(NEW))
        p1.start();p2.start()
        self.addCleanup(p1.stop)
        self.addCleanup(p2.stop)
        self.addCleanup(self.tmp.cleanup)
    def make(self):
        gq.prepare(self.base,self.orig,self.selected,self.out)

    def test_real_31_route_select_and_exact_rollback(self):
        self.make()
        _,old=gq.scan(self.base)
        _,new=gq.scan(self.out)
        self.assertEqual(len(old),31)
        self.assertEqual({route for route in old if old[route].read_bytes()!=new[route].read_bytes()}, {gq.ROUTE})
        self.assertEqual(new[gq.ROUTE].read_bytes(),NEW)
        self.assertEqual(old[gq.ROUTE].read_bytes(),OLD)
        p=self.root/"selected.rbxlx"
        make_place(self.out,p)
        gq.verify(self.base,self.out,self.orig,self.selected,p)
        receipt=json.loads((self.root/gq.RECEIPT).read_text())
        self.assertEqual(receipt["real_rojo_script_source_class_exact"],"31/31")
        self.assertEqual(receipt["new_scripts"],0)

    def test_reject_current_guard_drift(self):
        (self.root/"Guard.luau").write_text("return modified")
        with self.assertRaisesRegex(ValueError,"CURRENT_RC_GUARD"):
            self.make()

    def test_reject_original_author_drift(self):
        self.orig.write_text("modified")
        with self.assertRaisesRegex(ValueError,"ORIGINAL482"):
            self.make()

    def test_reject_selected_author_drift(self):
        self.selected.write_text("modified")
        with self.assertRaisesRegex(ValueError,"ORIGINAL611"):
            self.make()

    def test_reject_30_script_layout(self):
        j=json.loads(self.base.read_text())
        j["tree"]["ServerScriptService"].pop("OTHER_00")
        self.base.write_text(json.dumps(j))
        with self.assertRaisesRegex(ValueError,"SOURCE_COUNT"):
            self.make()

    def test_reject_duplicate_script_name_different_route(self):
        j=json.loads(self.base.read_text())
        j["tree"]["ReplicatedStorage"]={"OTHER_00":{"$path":"OTHER_00.luau"}}
        self.base.write_text(json.dumps(j))
        with self.assertRaisesRegex(ValueError,"SOURCE_COUNT"):
            self.make()

    def test_reject_existing_output(self):
        self.out.write_text("{}")
        with self.assertRaisesRegex(ValueError,"OUTPUT_MUST_BE_FRESH_SIBLING"):
            self.make()

    def test_reject_mutated_embedded_guard_place(self):
        self.make()
        place=self.root/"mutated.rbxlx"
        make_place(self.out,place)
        root=ET.fromstring(place.read_bytes())
        for n in root.iter("Item"):
            p=n.find("Properties")
            if p is not None and p.findtext("string[@name='Name']")=="EGGRUMBLE_InteractionGuard":
                p.find("ProtectedString[@name='Source']").text="return attacker"
        place.write_bytes(ET.tostring(root,encoding="utf-8"))
        with self.assertRaisesRegex(ValueError,"ACTUAL_ROJO_SCRIPT_SOURCE_OR_CLASS"):
            gq.verify(self.base,self.out,self.orig,self.selected,place)

if __name__=="__main__":main()
