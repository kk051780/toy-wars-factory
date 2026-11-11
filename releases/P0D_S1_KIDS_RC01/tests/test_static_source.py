import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class SourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=(ROOT/'src/server/Game.server.luau').read_text()
        cls.map=(ROOT/'src/server/MapBuilder.luau').read_text()
        cls.client=(ROOT/'src/client/HUD.client.luau').read_text()
        cls.rules=(ROOT/'src/server/S1Rules.luau').read_text()
        cls.config=(ROOT/'src/shared/Config.luau').read_text()
        cls.project=json.loads((ROOT/'default.project.json').read_text())

    def test_project_is_datamodel(self):self.assertEqual(self.project['tree']['$className'],'DataModel')
    def test_project_maps_server(self):self.assertEqual(self.project['tree']['ServerScriptService']['TrapRaidersS1']['$path'],'src/server')
    def test_project_maps_client(self):self.assertEqual(self.project['tree']['StarterPlayer']['StarterPlayerScripts']['TrapRaidersHUD']['$path'],'src/client/HUD.client.luau')
    def test_project_maps_shared(self):self.assertEqual(self.project['tree']['ReplicatedStorage']['TrapRaidersShared']['$path'],'src/shared')
    def test_single_remote_listener(self):self.assertEqual(len(re.findall(r'OnServerEvent:Connect',self.server)),1)
    def test_no_client_damage(self):self.assertNotIn('damage =',self.client)
    def test_no_client_coordinate_payload(self):self.assertNotRegex(self.client,r'remote:FireServer\(\{[^}]*Position')
    def test_no_client_target(self):self.assertNotIn('target =',self.client)
    def test_single_round_controller(self):self.assertEqual(self.server.count('local function tickRound'),1)
    def test_single_authoritative_canonical_server_roll(self):
        # The new v40+D08 event host needs exactly ONE trusted server roll.
        # It is invoked ONLY by the existing Game tick through original D08,
        # never by another scheduler, client target or separate server Script.
        self.assertEqual(self.server.count('math.random(0, 99)'),1)
        self.assertEqual(self.server.count('serverRoll = function(_matchId, _epoch)'),1)
        self.assertEqual(self.server.count('CanonicalHost.new('),1)
        self.assertNotIn('nextAlarmAt',self.server)
        self.assertNotIn('while true do\n        canonicalHost:tick()',self.server)
    def test_server_validates_seq(self):self.assertIn('Rules.validSeq',self.server)
    def test_server_validates_distance(self):self.assertIn('Config.InteractDistance',self.server)
    def test_server_validates_aim(self):self.assertIn('look:Dot',self.server)
    def test_line_of_sight_for_players(self):self.assertIn('workspace:Raycast',self.server)
    def test_no_client_target_damage(self):self.assertIn('hum:TakeDamage(Config.CombatDamage',self.server)
    def test_role_change_prevents_heal(self):self.assertIn('if match.phase == "ACTIVE" then return end',self.server)
    def test_egg_drops_on_death(self):self.assertIn('hum.Died:Connect',self.server)
    def test_egg_drops_on_disconnect(self):self.assertIn('Players.PlayerRemoving:Connect',self.server)
    def test_reward_source_absent(self):self.assertNotIn('DataStoreService',self.server)
    def test_no_remote_from_map(self):self.assertNotIn('RemoteEvent',self.map)
    def test_ui_supports_mobile_tap(self):self.assertIn('MouseButton1Click',self.client)
    def test_ui_supports_keyboard(self):self.assertIn('Enum.KeyCode.F',self.client)
    def test_map_is_procedural(self):self.assertIn('Instance.new("Part")',self.map)
    def test_map_has_two_eggs(self):self.assertIn('name .. "_EGG"',self.map)
    def test_map_has_scorepads(self):self.assertIn('name .. "_SCORE_PAD"',self.map)
    def test_no_external_asset_urls(self):
        alltext=self.server+self.map+self.client+self.rules+self.config
        self.assertNotRegex(alltext,r'(https?://|rbxassetid://|require\s*\(\s*\d+)')
    def test_no_public_secret(self):
        for f in ROOT.rglob('*.luau'):
            self.assertNotRegex(f.read_text(),r'(?i)(secret[_-]?key\s*=|private[_-]?key\s*=|token\s*=\s*"[A-Za-z0-9]{28})')
    def test_single_server_guardian_trap_authority(self):
        trap=(ROOT/"src/server/S1TrapRules.luau").read_text()
        self.assertIn('elseif data.action == "PLACE_TRAP" then placeTrap(player, data)',self.server)
        self.assertEqual(self.server.count("OnServerEvent:Connect"),1)
        self.assertIn("TrapRules.canPlace",self.server)
        self.assertIn("TrapRules.shouldTrigger",self.server)
        self.assertIn('role ~= "GUARDIAN"',trap)
        self.assertIn("slowSpeed",trap)
        self.assertNotIn("FireServer",trap)
        self.assertNotIn("RemoteEvent",trap)
        self.assertNotIn("DataStoreService",trap)
    def test_mobile_guardian_trap_intent_no_coordinates(self):
        self.assertIn('action("PLACE_TRAP", nil)',self.client)
        self.assertIn("Enum.KeyCode.T",self.client)
        self.assertNotIn("Vector3.new",self.client)
    def test_no_roblox_live_publish(self):self.assertNotIn('Publish',self.server)
    def test_rojo_file_suffixes(self):self.assertTrue((ROOT/'src/server/Game.server.luau').is_file() and (ROOT/'src/client/HUD.client.luau').is_file())

if __name__ == '__main__':unittest.main()
