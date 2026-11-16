"""New 26→27 composition contract and fail-closed negative cases."""
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import compose_private27 as M

class Private27ContractTests(unittest.TestCase):
    def test_author_provenance_is_4_fixed_original_authors(self):
        self.assertEqual(set(M.AUTHOR_26), {"game","spatial","art","score"})
        for ident, pinned in M.AUTHOR_26.values():
            self.assertTrue(ident.startswith("#"))
            self.assertEqual(len(pinned), 40)

    def test_existing_art_score_7role_8lane_scope_is_present(self):
        self.assertEqual(M.TOTAL,26)
        self.assertEqual(M.SERVER_COUNT,23)
        self.assertEqual(M.CLIENT_COUNT,3)
        self.assertEqual(len(M.EXPECTED),16)
        self.assertEqual(sum(M.EXPECTED.values()),21)
        self.assertIn("EGGRUMBLE_MatchResultService.luau",M.EXPECTED)
        self.assertIn("EGGRUMBLE_FlagshipFieldArt.server.luau",M.EXPECTED)

    def test_server_and_client_gate_emission_uses_existing_owner_only(self):
        source="--!strict\nlocal RunService=game:GetService('RunService')\nif not RunService:IsStudio() then return end\n"
        server,changed=M.overlay(source,"EGGRUMBLE_HeroSilhouetteArt","EGGRUMBLE_HeroSilhouetteArt.server.luau")
        client,n=M.overlay(source,"EGGRUMBLE_ArtDistanceLOD","EGGRUMBLE_ArtDistanceLOD.client.luau")
        host_source=source+M.compose.WORLD_MARKER+"\n"+M.compose.BOOT_DONE_MARKER+"\n"
        host,_=M.overlay(host_source,"EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_LobbyCastleModesPreview.server.luau")
        self.assertEqual(changed,1)
        self.assertEqual(n,1)
        self.assertIn("PrivateGate.allowed()",server)
        self.assertIn("PrivateGate.waitAllowed(8)",client)
        self.assertIn(M.compose.BOOT_READY,host)
        self.assertIn("if not PrivateGate.allowed() then return end",host)
        self.assertLess(host.index(M.compose.WORLD_WATCH),host.index(M.compose.BOOT_READY))
        self.assertEqual(host.count(M.compose.WORLD_WATCH),1)
        self.assertIn("PrivateGate.watchWorld(folder)",host)
        for out in (server,client,host):
            self.assertNotIn("RunService:IsStudio()",out)
            self.assertIn("EGGRUMBLE_PrivateLiveGate",out)

    def test_guard_drift_is_red_not_widened(self):
        with self.assertRaises(ValueError):
            M.overlay("--!strict\nreturn {}\n","EGGRUMBLE_ArtDistanceLOD","EGGRUMBLE_ArtDistanceLOD.client.luau")
        with self.assertRaises(ValueError):
            M.overlay("--!strict\nif RunService:IsStudio() then return end\n","EGGRUMBLE_CastleMatchRules","EGGRUMBLE_CastleMatchRules.luau")
        with self.assertRaises(ValueError):
            M.overlay("local x=RunService:IsStudio()\n","EGGRUMBLE_BotActors","EGGRUMBLE_BotActors.luau")

    def test_host_lease_watch_fails_closed_on_moved_anchor(self):
        source="--!strict\nif not RunService:IsStudio() then return end\n"
        with self.assertRaises(ValueError):
            M.overlay(source,"EGGRUMBLE_LobbyCastleModesPreview",
                      "EGGRUMBLE_LobbyCastleModesPreview.server.luau")


    def test_private_gate_one_host_authority_and_irreversible_revoke(self):
        gate=(M.compose.HERE/"EGGRUMBLE_PrivateLiveGate.luau").read_text(encoding="utf-8")
        self.assertIn("local activeWorld:Instance?=nil",gate)
        self.assertIn("local permanentlyRevoked=false",gate)
        self.assertIn("GetAttributeChangedSignal(Gate.OPT_IN_ATTRIBUTE)",gate)
        self.assertIn("if activeWorld~=world and world.Parent then world:Destroy() end",gate)
        self.assertIn("permanentlyRevoked=true",gate)
        self.assertIn("if not RunService:IsStudio() and (not activeWorld or not activeWorld.Parent)",gate)
        self.assertLess(gate.index("ReplicatedStorage:SetAttribute(Gate.READY_ATTRIBUTE,false)"),gate.index("if world.Parent then world:Destroy() end"))

    def test_unprotected_author_script_is_byte_identical(self):
        raw="--!strict\nreturn {someOriginalGameAuthority=true}\n"
        out, n=M.overlay(raw,"EGGRUMBLE_CastleMatchRules","EGGRUMBLE_CastleMatchRules.luau")
        self.assertEqual((out,n),(raw,0))

    def test_generated_composite_cannot_go_inside_repo(self):
        with self.assertRaises(ValueError):
            M.build(M.compose.PROJECT,M.compose.HERE/"EGGRUMBLE_PrivateLiveGate.luau",
                    M.compose.REPO/"danger")

if __name__=="__main__":
    unittest.main()
