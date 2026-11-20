#!/usr/bin/env python3
"""Synthetic structural/mutation tests; separate CI uses genuine official31 Luau/Rojo."""
import json
import tempfile
import unittest
from pathlib import Path
from compose_rehearsal36 import compose,flatten,HOST,CORE,REGEN

BASE_NAMES=["EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_SevenRoleCombat",
            "EGGRUMBLE_SwarmCombat"]+["Base%02d"%i for i in range(28)]
HOST_BODY='''local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))
local function begin(session,p,role)
 SevenRoleCombat.equip(session,p,role)
 task.delay(1,function()
  SevenRoleCombat.equip(session,p,role)
 end)
end
'''
REQUIRE='local NaturalRegen=require(script.Parent:WaitForChild("EGGRUMBLE_NaturalRegen"))'
def setup(root):
    projects=[]
    for stage in ("base31","regen33","realm34"):
        directory=root/stage
        directory.mkdir()
        server={}
        for name in BASE_NAMES:
            src=HOST_BODY if name==BASE_NAMES[0] else ("return {name="+repr(name)+"}\n")
            if stage=="regen33" and name==BASE_NAMES[0]:
                anchor='local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))'
                src=src.replace(anchor,anchor+"\n"+REQUIRE)
                src=src.replace(' SevenRoleCombat.equip(session,p,role)\n',
                    ' SevenRoleCombat.equip(session,p,role)\n NaturalRegen.attach(session,p,role)\n')
                src=src.replace('  SevenRoleCombat.equip(session,p,role)\n',
                    '  SevenRoleCombat.equip(session,p,role)\n  NaturalRegen.attach(session,p,role)\n')
                # Previous replacement produces a nested duplicate when replacing
                # the one-space prefix inside two-space indent: restore exact two hooks.
                src=HOST_BODY.replace(anchor,anchor+"\n"+REQUIRE)
                src=src.replace(' SevenRoleCombat.equip(session,p,role)\n',
                    ' SevenRoleCombat.equip(session,p,role)\n NaturalRegen.attach(session,p,role)\n',1)
                src=src.replace('  SevenRoleCombat.equip(session,p,role)\n',
                    '  SevenRoleCombat.equip(session,p,role)\n  NaturalRegen.attach(session,p,role)\n',1)
            file=directory/(name+".luau")
            file.write_text(src,encoding="utf-8")
            server[name]={"$path":file.name}
        tree={"ServerScriptService":server}
        if stage=="regen33":
            for route in REGEN:
                file=directory/(route[-1]+".luau")
                file.write_text("return {}\n",encoding="utf-8")
                server[route[-1]]={"$path":file.name}
        if stage=="realm34":
            for route in CORE:
                file=directory/(route[-1]+(".client.luau" if route[0]=="StarterPlayer" else ".server.luau"))
                file.write_text("return {}\n",encoding="utf-8")
                node=tree
                for name in route[:-1]:node=node.setdefault(name,{})
                node[route[-1]]={"$path":file.name}
        project=directory/(stage+".project.json")
        # If module has a nested StarterPlayerScripts path, its file is still relative
        # to the project directory; the produced Rojo class is intentionally synthetic.
        project.write_text(json.dumps({"name":stage,"tree":tree}),encoding="utf-8")
        projects.append(project)
    return projects

class CrosslaneGate(unittest.TestCase):
    def test_rehearsal36_and_off31(self):
        with tempfile.TemporaryDirectory() as tmp:
            b,r,a=setup(Path(tmp))
            out=Path(tmp)/"combined/dual36.project.json"
            compose(b,r,a,out)
            _,combo=flatten(out)
            self.assertEqual(len(combo),36)
            _,base=flatten(b)
            for k in base:
                if k!=HOST:self.assertEqual(combo[k].read_bytes(),base[k].read_bytes())
            self.assertTrue(out.with_suffix(".receipt.json").is_file())
    def test_reject_realm_changed_original31(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);b,r,a=setup(root)
            path=a.parent/"Base00.luau"
            path.write_text("-- altered in realm branch\n")
            with self.assertRaisesRegex(ValueError,"RED_REALM_MUTATED_BASE"):
                compose(b,r,a,root/"out/project.json")
    def test_reject_regen_changed_combat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);b,r,a=setup(root)
            (r.parent/"EGGRUMBLE_SevenRoleCombat.luau").write_text("return {bad=true}\n")
            with self.assertRaisesRegex(ValueError,"RED_REGEN_MUTATED_BASE"):
                compose(b,r,a,root/"out/project.json")
    def test_reject_extra_host_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);b,r,a=setup(root)
            host=r.parent/"EGGRUMBLE_LobbyCastleModesPreview.luau"
            host.write_text(host.read_text()+"NaturalRegen.attach(session,p,role)\n")
            with self.assertRaisesRegex(ValueError,"RED_MISSING_REGEN_HOST_RUNTIME"):
                compose(b,r,a,root/"out/project.json")
    def test_reject_missing_realm_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);b,r,a=setup(root)
            obj=json.loads(a.read_text())
            del obj["tree"]["ServerScriptService"]["EGGRUMBLE_RealmBattleCore"]
            a.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"RED_UNEXPECTED_SOURCE_COUNT"):
                compose(b,r,a,root/"out/project.json")
    def test_reject_missing_regen_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);b,r,a=setup(root)
            host=r.parent/"EGGRUMBLE_LobbyCastleModesPreview.luau"
            host.write_text(host.read_text().replace(REQUIRE+"\n",""))
            with self.assertRaisesRegex(ValueError,"RED_MISSING_REGEN_HOST_RUNTIME"):
                compose(b,r,a,root/"out/project.json")

if __name__=="__main__":
    unittest.main()
