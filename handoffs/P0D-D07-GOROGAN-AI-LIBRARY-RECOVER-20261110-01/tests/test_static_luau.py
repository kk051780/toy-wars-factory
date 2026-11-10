import pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
core=(ROOT/'luau/GoroganServerAICore.luau').read_text()
runtime=(ROOT/'luau/GoroganServerRuntime.luau').read_text()
class StaticContractTests(unittest.TestCase):
    def test_luau_core_module_present(self):self.assertIn('return Core',core)
    def test_pure_no_game_mutation(self):
        for forbidden in ['TakeDamage(', 'Instance.new(', 'PathfindingService','DataStoreService','HttpService','MarketplaceService']:
            self.assertNotIn(forbidden,core)
    def test_runtime_no_remote_connection(self):
        for forbidden in ['OnServerEvent:Connect(', 'RemoteEvent.new(', 'FireServer(', 'MarketplaceService']:
            self.assertNotIn(forbidden,runtime)
    def test_boss_stage_restricted(self):
        self.assertIn('input.stageId ~= "S1" and input.stageId ~= "S3"',core)
    def test_event_choice_external(self):self.assertIn('ownerOf(input)',core);self.assertIn('kind == "BOSS"',core)
    def test_attack_windup_2s(self):self.assertIn('WINDUP=2',core)
    def test_damage_bounded_8(self):self.assertIn('DAMAGE=8',core)
    def test_radius_bounded_7(self):self.assertIn('RADIUS=7',core)
    def test_stomps_max_three(self):self.assertIn('MAX_STOMPS=3',core)
    def test_ttl_matches_visual(self):self.assertIn('TTL=14',core)
    def test_move_intent_not_teleport(self):
        self.assertIn('CHASE_STEP=8',core);self.assertNotIn('CFrame=',core)
    def test_neutral_both_teams(self):self.assertIn('p.team == "BLUE" or p.team == "RED"',core)
    def test_runtime_true_los(self):self.assertIn('isLineOfSight(cmd.center,p)==true',runtime)
    def test_runtime_reacquire_roster(self):self.assertIn('local fresh=self.deps.getRoster()',runtime)
    def test_authority_requires_server_callbacks(self):
        self.assertIn('isCanonicalBossActivation',runtime);self.assertIn('isRoundActive',runtime)
    def test_no_new_event_selector(self):
        self.assertNotIn('math.random',core+runtime);self.assertNotIn('classify(',core+runtime)
    def test_visual_matches_prior_packet(self):
        for v in ['"START"','"STOMP"','"END"']:
            self.assertIn(v,runtime)
    def test_server_damage_adapter_only(self):
        self.assertIn('applyServerDamage(',runtime)
        self.assertNotIn('Humanoid:TakeDamage',runtime)
if __name__=='__main__':unittest.main()
