"""Source-exact offline checks; native Luau/real Rojo are separate GitHub CI gates."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.compose_private22 import compose, MODULE, HOST, ORIGINAL, REQUIRE

class SourceContract(unittest.TestCase):
    def make_author(self,base):
        author=base/"author"
        author.mkdir()
        server={"$className":"ServerScriptService"}
        for i in range(19):
            name=HOST if i==0 else f"Mock{i}.luau"
            server[f"Script{i}"]={"$path":name}
            src=REQUIRE+ "local function startSession(mode:string)\nend\n" +ORIGINAL if i==0 else "return {}\n"
            (author/name).write_text(src)
        client={"$className":"StarterPlayerScripts"}
        for i in range(2):
            name=f"Client{i}.client.luau"
            client[f"Client{i}"]={"$path":name}
            (author/name).write_text("print('client')\n")
        project={"name":"test","tree":{"$className":"DataModel",
            "ServerScriptService":server,"StarterPlayer":{"StarterPlayerScripts":client}}}
        (author/"EGGRUMBLE_V3_STUDIO.project.json").write_text(json.dumps(project))
        return author

    def test_private_composition_no_author_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            author=self.make_author(base)
            old={s.name:s.read_bytes() for s in author.iterdir() if s.is_file()}
            out=base/"private"
            project=compose(author,out)
            receipt=json.loads((out/"SOURCE22_RECEIPT.json").read_text())
            self.assertEqual(receipt["original_source_count"],21)
            self.assertEqual(receipt["candidate_source_count"],22)
            self.assertEqual(len(receipt["candidate"]),22)
            self.assertEqual(len(receipt["author_original"]),21)
            self.assertEqual(receipt["only_changed_original"],[HOST])
            self.assertEqual({s.name:s.read_bytes() for s in author.iterdir() if s.is_file()},old)
            host=(out/"src"/HOST).read_text()
            self.assertIn("DropBounds.recover(mode,root.X,root.Z,at.X,at.Z",host)
            self.assertIn("safe.z+17",host)
            self.assertEqual(host.count("local DropBounds=require("),1)
            for name in receipt["author_original"]:
                if name!=HOST:
                    self.assertEqual((out/"src"/name).read_bytes(),(author/name).read_bytes())
            tree=json.loads(project.read_text())["tree"]
            self.assertIn("EGGRUMBLE_FieldEggDropBounds",tree["ServerScriptService"])

    def test_reject_out_of_date_host(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            author=self.make_author(base)
            path=author/HOST
            path.write_text(path.read_text().replace(ORIGINAL,"local landing=nil"))
            with self.assertRaises(AssertionError):
                compose(author,base/"private")
    
    def test_reject_in_place_write(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            author=self.make_author(base)
            with self.assertRaises(ValueError):
                compose(author,author)

    def test_real_policy_is_only_one_pure_source(self):
        policy=MODULE.read_text()
        self.assertEqual(policy.count("function Drop.recover("),1)
        self.assertIn('WORLD_X={TEAM=-620,BATTLE_ROYALE=620}',policy)
        self.assertIn("MARGIN=40",policy)
        self.assertNotIn("DataStore",policy)
        self.assertNotIn("FireServer",policy)

if __name__=="__main__":
    unittest.main()
