import tempfile,unittest,json
from pathlib import Path
from xml.etree import ElementTree as ET
from resolve_current31 import canonical_scripts,resolve,RedGate

def mapping(obj,p):
    d={}
    for n,v in obj["tree"]["ServerScriptService"].items():
        d[n]=((p.parent/v["$path"]).resolve(strict=True),"Script")
    return d

class CanonicalSourceMatch(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.root.joinpath("artifacts").mkdir()
        self.source=self.root/"artifacts/src"
        self.source.mkdir()
        self.proj=self.root/"artifacts/after.latest.project.json"
        nodes={}
        root=ET.Element("roblox")
        for i in range(31):
            name=f"Script{i:02d}"
            src=f"actual-{i}"
            (self.source/(name+".server.luau")).write_text(src)
            nodes[name]={"$path":"src/"+name+".server.luau"}
            item=ET.SubElement(root,"Item",{"class":"Script"})
            props=ET.SubElement(item,"Properties")
            ET.SubElement(props,"string",{"name":"Name"}).text=name
            ET.SubElement(props,"ProtectedString",{"name":"Source"}).text=src
        self.place=self.root/"canonical.rbxlx"
        self.place.write_bytes(ET.tostring(root,encoding="utf-8"))
        self.proj.write_text(json.dumps({"tree":{"ServerScriptService":nodes}}))
    def test_true_complete_31_matches(self):
        path,sources,allmatch=resolve(self.place,self.root/"artifacts",mapping)
        self.assertEqual(path,self.proj)
        self.assertEqual(len(sources),31)
        self.assertEqual(len(allmatch),1)
    def test_wrong_stale_source_fails_closed(self):
        (self.source/"Script03.server.luau").write_text("stale-pre-shield")
        with self.assertRaisesRegex(RedGate,"RED_.*NO_FINAL"):resolve(self.place,self.root/"artifacts",mapping)
    def test_missing_script_fails_closed(self):
        obj=json.loads(self.proj.read_text())
        del obj["tree"]["ServerScriptService"]["Script30"]
        self.proj.write_text(json.dumps(obj))
        with self.assertRaises(RedGate):resolve(self.place,self.root/"artifacts",mapping)
    def test_no_duplicate_canonical_name(self):
        root=ET.parse(self.place).getroot()
        root.append(ET.fromstring(ET.tostring(next(root.iter("Item")))))
        self.place.write_bytes(ET.tostring(root))
        with self.assertRaises(RedGate):canonical_scripts(self.place)
    def test_second_equivalent_project_is_safe(self):
        another=self.root/"artifacts/z_copy.project.json"
        another.write_text(self.proj.read_text())
        _,_,matches=resolve(self.place,self.root/"artifacts",mapping)
        self.assertEqual(len(matches),2)
        self.assertEqual(matches[-1],another)
if __name__=="__main__":unittest.main()
