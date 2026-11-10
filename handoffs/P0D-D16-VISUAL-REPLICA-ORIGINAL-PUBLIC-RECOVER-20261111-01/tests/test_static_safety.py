import pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
CLIENT=(ROOT/'src'/'ScaleVisualReplica.luau').read_text()
BOOT=(ROOT/'src'/'ScaleFxClientBootstrap.client.luau').read_text()
POLICY=(ROOT/'src'/'ScaleFxClientPolicy.luau').read_text()
BRIDGE=(ROOT/'src'/'ScaleFxSnapshotBridge.luau').read_text()
class StaticSafetyTests(unittest.TestCase):
    def test_no_network_sends(self):
        for text in (CLIENT,BOOT,POLICY,BRIDGE):
            for forbidden in ('FireServer(', 'InvokeServer(', 'FireAllClients(', 'SetAttribute(', 'TakeDamage(', 'HumanoidDescription'):
                with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden,text)
    def test_no_character_scaling(self):
        for bad in ('ApplyDescription(', 'ScaleTo(', 'WalkSpeed =', 'MaxHealth =', '.Health =', 'LocalTransparencyModifier ='):
            with self.subTest(bad=bad): self.assertNotIn(bad,CLIENT)
    def test_clone_physics_are_off(self):
        for snippet in ('clone.Anchored = true','clone.CanCollide, clone.CanTouch, clone.CanQuery = false, false, false','clone.CastShadow = false','clone.Massless = true'):
            self.assertIn(snippet,CLIENT)
    def test_no_server_scripts_in_clones(self):self.assertIn('descendant:Destroy()',CLIENT)
    def test_bounded_work(self):
        self.assertIn('MAX_VISIBLE_PLAYERS = 8',CLIENT)
        self.assertIn('MAX_PARTS_PER_PLAYER = 18',CLIENT)
        self.assertIn('MAX_DISTANCE = 90',CLIENT)
    def test_cleanup_connections(self):
        self.assertIn('c:Disconnect()',CLIENT)
        self.assertIn('self.folder:Destroy()',CLIENT)
        self.assertIn('self:_clear()',CLIENT)
    def test_client_policy_declines_second_chooser(self):
        self.assertIn('SECOND_EVENT_REJECTED',POLICY)
        self.assertIn('TARGET_ADDED_AFTER_START',POLICY)
        self.assertIn('math.min(state.deadline, nextDeadline)',POLICY)
    def test_bridge_uses_round_elapsed_only(self):
        self.assertIn('snapshot.expiresAt - elapsedSeconds',BRIDGE)
        self.assertNotIn('os.clock()',BRIDGE)
        self.assertNotIn('GetServerTimeNow',BRIDGE)
    def test_expires_from_ttl_not_server_clock(self):
        self.assertIn('packet.remainingSeconds',POLICY)
        self.assertIn('os.clock()',CLIENT)
        self.assertNotIn('GetServerTimeNow',CLIENT)
    def test_remote_recv_only(self):
        self.assertIn('remote.OnClientEvent:Connect',CLIENT)
        self.assertNotIn('OnServerEvent',CLIENT)
    def test_optional_bootstrap_no_unbounded_wait(self):
        self.assertIn('FindFirstChild',BOOT)
        self.assertNotIn('WaitForChild(',BOOT)

if __name__=='__main__':unittest.main()
