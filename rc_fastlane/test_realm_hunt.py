#!/usr/bin/env python3
"""Small non-duplicate, fail-closed contract tests for the optional feature."""
import hashlib
import json
import unittest
from pathlib import Path
BASE=Path(__file__).resolve().parent
def gitblob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

class RealmHuntContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flags=json.loads((BASE/"FEATURE_SWITCHES.json").read_text("utf8"))
        cls.records=cls.flags["features"]["REALM_HUNT_V1"]["source"]
        cls.parts=[(x,(BASE.parent/x["path"]).read_text("utf8")) for x in cls.records]
    def test_unique_source_paths_and_git_blob_pins(self):
        self.assertEqual(len(self.records),2)
        self.assertEqual(len({x["dest"] for x in self.records}),2)
        for item,txt in self.parts:
            self.assertEqual(gitblob(txt.encode("utf8")),item["blob"])
    def test_studio_only_and_no_authority_collision(self):
        for item,txt in self.parts:
            self.assertIn('if not RunService:IsStudio() then return end',txt)
            for forbidden in ("DataStoreService","GetDataStore(","UpdateAsync(",
                              "FireServer(","OnServerEvent:Connect(",
                              'Instance.new("RemoteEvent")',"MarketplaceService",
                              "PromptProductPurchase(","TakeDamage(","WalkSpeed =","JumpPower ="):
                self.assertNotIn(forbidden,txt)
    def test_real_server_distance_and_death_checks(self):
        server=self.parts[0][1]
        for check in ("player.Parent~=Players","humanoid.Health<=0",
                      "(root.Position-item.position).Magnitude>15",
                      "prompt.Triggered:Connect(function(player)",
                      "record.found[item.id]","record.count==#LANDMARKS"):
            self.assertIn(check,server)
    def test_four_accessible_zones_and_no_collision(self):
        server=self.parts[0][1]
        for key in ('id="SKY"','id="SEA"','id="EMBER"','id="STAR"'):
            self.assertIn(key,server)
        self.assertIn("core.CanCollide=false",server)
        self.assertIn("ring.CanCollide=false",server)
        self.assertIn("local LANDMARKS",server)
        self.assertIn("COSMETIC_ONLY",server)
    def test_readonly_client_counter(self):
        client=self.parts[1][1]
        self.assertIn('GetAttributeChangedSignal(prefix..key)',client)
        self.assertIn('math.clamp(math.floor(n),0,4)',client)
        self.assertIn("card.Visible=enabled",client)
        self.assertNotIn("SetAttribute(",client)
        self.assertNotIn("RemoteEvent",client)

if __name__=="__main__":
    unittest.main()
