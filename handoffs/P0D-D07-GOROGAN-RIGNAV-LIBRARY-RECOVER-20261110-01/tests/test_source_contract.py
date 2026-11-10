import pathlib,unittest,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
rig=(ROOT/'luau/GoroganRigDriver.luau').read_text()
damage=(ROOT/'luau/GoroganDamageBoundary.luau').read_text()
class TestLuaStatic(unittest.TestCase):
    def test_server_pathfinding(self):self.assertIn('PathfindingService:CreatePath',rig)
    def test_server_ownership(self):self.assertIn('SetNetworkOwner(nil)',rig)
    def test_no_client_remote(self):
        self.assertNotRegex(rig+damage,r'OnServerEvent|FireServer\(|InvokeServer\(')
    def test_rig_type(self):self.assertIn('Enum.HumanoidRigType.R6',rig)
    def test_driver_ttl(self):self.assertIn('MAX_LIFETIME=14',rig)
    def test_rate_budget(self):self.assertIn('MAX_NAV=20',rig);self.assertIn('NAV_MIN_GAP=.75',rig)
    def test_async_yield_rereview(self):self.assertIn('STALE_AFTER_YIELD',rig);self.assertIn('self.deps.currentRound()==thisRound',rig)
    def test_no_teleport_nav(self):
        x=rig.split('function Driver:requestNavigation')[1];self.assertNotIn(':PivotTo(',x)
    def test_failclosed_terrain(self):self.assertIn('self.deps.isSafeTerrain(snapshot.groundPosition)~=true',rig)
    def test_damage_cap(self):self.assertIn('damage>8',damage)
    def test_damage_los(self):self.assertIn('workspace:Raycast',damage);self.assertIn('BLOCKED_LOS',damage)
    def test_actual_damage(self):self.assertIn('hum:TakeDamage(damage)',damage)
    def test_damage_duplicate(self):self.assertIn('self.receipts[key]',damage)
    def test_damage_epoch(self):self.assertIn('isRealRoundEvent(roundId,eventId)',damage)
    def test_damage_attestation(self):self.assertIn('isCanonicalAttackReceipt(roundId,eventId,attackId)',damage)
    def test_no_datastore(self):self.assertNotIn('DataStoreService',rig+damage)
    def test_ignore_no_client_choice(self):self.assertNotIn('PlayerGui',rig+damage)
    def test_disabled_default(self):self.assertEqual((rig+damage).count('DISABLED_UNTIL_OWNER_PC_REVIEW'),2)
