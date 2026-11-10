from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
POLICY=(ROOT/'luau/RiderMountPolicy.luau').read_text()
ADAPTER=(ROOT/'luau/RiderMountServerAdapter.luau').read_text()
class StaticLuauContractTests(unittest.TestCase):
    def test_returns_module_policy(self):self.assertTrue(POLICY.rstrip().endswith('return M'))
    def test_returns_module_adapter(self):self.assertTrue(ADAPTER.rstrip().endswith('return Adapter'))
    def test_no_remotes(self):
        self.assertNotIn('OnServerEvent',POLICY+ADAPTER)
        self.assertNotIn('FireServer',POLICY+ADAPTER)
    def test_default_disabled(self):self.assertIn('enabled=false',ADAPTER)
    def test_role_cap(self):self.assertIn('"DRIVER", "PASSENGER"',POLICY)
    def test_lease(self):self.assertIn('LEASE_MS = 1500',POLICY)
    def test_fresh_timestamp(self):self.assertIn('MAX_SNAPSHOT_AGE_MS = 350',POLICY)
    def test_epoch(self):self.assertIn('authorityEpoch',POLICY)
    def test_character_generation(self):self.assertIn('characterEpoch',POLICY+ADAPTER)
    def test_mount_owner(self):self.assertIn('getTrustedSnapshot',ADAPTER)
    def test_physical_weld_explicit(self):self.assertIn('WeldConstraint',ADAPTER)
    def test_physical_mount_limited(self):self.assertIn('MAX_SEAT_DISTANCE_STUDS',ADAPTER)
    def test_cleanup(self):self.assertIn('function Adapter:close()',ADAPTER);self.assertIn('Destroy()',ADAPTER)
    def test_closed_driver_unmount(self):self.assertIn('self:_detach("DRIVER")',ADAPTER)
    def test_closed_passenger_unmount(self):self.assertIn('self:_detach("PASSENGER")',ADAPTER)
    def test_mount_failed_closed(self):self.assertIn('PHYSICAL_DRIVER_MOUNT_FAILED',ADAPTER)
    def test_no_network_owner_override(self):self.assertNotIn('SetNetworkOwner',ADAPTER)
    def test_no_humanoid_damage(self):self.assertNotIn('TakeDamage(',ADAPTER)
    def test_no_server_studio_references(self):self.assertNotIn('Studio',POLICY)
