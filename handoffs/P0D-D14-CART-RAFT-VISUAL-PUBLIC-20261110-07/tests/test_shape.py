from pathlib import Path
import unittest
ROOT=Path(__file__).parents[1]

class Shape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=(ROOT/'src/VehicleVisualPolicy.luau').read_text()
        cls.m=(ROOT/'src/VehicleVisualModels.luau').read_text()
        cls.c=(ROOT/'src/VehicleVisualClient.luau').read_text()

    def test_luau_modules_three(self):self.assertEqual(len(list((ROOT/'src').glob('*.luau'))),3)
    def test_local_only(self):self.assertIn('OnClientEvent',self.c)
    def test_no_fire_server(self):self.assertNotIn(':FireServer(',self.c)
    def test_no_server_receiver(self):self.assertNotIn('OnServerEvent',self.c)
    def test_explicit_optin(self):self.assertIn('options.enabled ~= true',self.c)
    def test_remote_is_instance(self):self.assertIn('serverRemote:IsA("RemoteEvent")',self.c)
    def test_uses_runservice(self):self.assertIn('RunService.Heartbeat',self.c)
    def test_owns_folder(self):self.assertIn('P0D_D14_VisualOnly',self.c)
    def test_closed_cleanup(self):self.assertIn('self.folder:Destroy()',self.c)
    def test_no_server_scripts(self):self.assertNotIn('ServerScriptService',self.c)
    def test_no_humanoid(self):self.assertNotIn('Humanoid',self.m)
    def test_no_real_vehicle_seat(self):self.assertNotIn('Instance.new("VehicleSeat")',self.m)
    def test_no_real_seat(self):self.assertNotIn('Instance.new("Seat")',self.m)
    def test_no_constraints(self):self.assertNotIn('Instance.new("WeldConstraint")',self.m)
    def test_no_collisions(self):self.assertIn('p.CanCollide = false',self.m)
    def test_no_touch(self):self.assertIn('p.CanTouch = false',self.m)
    def test_no_query(self):self.assertIn('p.CanQuery = false',self.m)
    def test_anchor(self):self.assertIn('p.Anchored = true',self.m)
    def test_nomotion(self):self.assertNotIn('AssemblyLinearVelocity',self.m)
    def test_two_models(self):self.assertIn('vehicleType == "CART"',self.m)
    def test_low_detail(self):self.assertIn('if not lowDetail then',self.m)
    def test_two_seat_badge(self):self.assertIn('"/2"',self.m)
    def test_bounded_four(self):self.assertIn('local LIMIT = 4',self.p)
    def test_ttl_bounded(self):self.assertIn('local MAX_TTL_MS = 20000',self.p)
    def test_stale_rejection(self):self.assertIn('packet.seq <= s.lastSeq',self.p)
    def test_move_unknown_reject(self):self.assertIn('kind == "UPDATE" and previous == nil',self.p)
    def test_round_end(self):self.assertIn('kind == "ROUND_END"',self.p)
    def test_no_remote_in_policy(self):self.assertNotIn('RemoteEvent',self.p)
    def test_no_public_key(self):self.assertNotIn('CHAT_CODEX_HANDOFF_KEY',self.p)
    def test_no_loadstring(self):self.assertNotIn('loadstring',self.p+self.m+self.c)
    def test_client_limit(self):self.assertIn('now - self.clock < 0.25',self.c)
    def test_no_datastore(self):self.assertNotIn('DataStoreService',self.c+self.m+self.p)
    def test_no_http(self):self.assertNotIn('HttpService',self.c+self.m+self.p)

if __name__=='__main__':unittest.main()
