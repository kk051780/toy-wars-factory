import pathlib,unittest
CORE=pathlib.Path(__file__).resolve().parents[1]/'luau'/'D16ScaleD08DispatchGate.luau'
D08_NAMED={'WX01_METEOR','WX02_SMALL','WX03_CROWN','WX04_GLIDE','WX05_CLOCK'}
class LuauContractTests(unittest.TestCase):
    def test_contract_symbols(self):
        s=CORE.read_text(encoding='utf8')
        for token in ['function Gate.new','function Gate:onWeatherActivate','function Gate:onCleanup','function Gate:snapshot','function Gate:stop','approvedByOwner == true','visualRendererReady == true','approvedSubtypeEffects','self.core.begin','self.core.snapshot','self.core.close','ROUND_CHANGED_DURING_CALLBACK','ROSTER_CHANGED','INVALID_EVENT_DEADLINE']:
            with self.subTest(token=token):self.assertIn(token,s)
    def test_match_d08_envelope(self):
        s=CORE.read_text()
        for token in ('event.kind ~= "WEATHER"','event.phase ~= "ACTIVATE"','event.validUntil','event.matchId','event.stage','event.epoch','event.subtype'):
            with self.subTest(token=token):self.assertIn(token,s)
    def test_explicit_approval_no_default_mapping(self):
        s=CORE.read_text()
        self.assertNotIn('approvedSubtypeEffects = {',s)
        self.assertNotIn('WX02_SMALL = "MINI_ALL"',s)
        self.assertNotIn('WX03_CROWN = "GIANT_ONE"',s)
    def test_weather_names(self):
        s=CORE.read_text()
        for token in D08_NAMED:self.assertIn(token+' = true',s)
    def test_no_second_chooser_or_side_effects(self):
        s=CORE.read_text()
        forbidden=('math.random','Random.new','Heartbeat:Connect','RunService',
            'task.spawn','task.delay','OnServerEvent','RemoteEvent',
            'Instance.new','Humanoid','TakeDamage','BodyScale','MarketplaceService',
            'SetPrimaryPartCFrame','AssemblyLinearVelocity')
        # Check executable source excluding comments, as README comments can name forbidden APIs.
        code='\n'.join(line for line in s.splitlines() if not line.lstrip().startswith('--'))
        for token in forbidden:
            with self.subTest(token=token):self.assertNotIn(token,code)
    def test_no_legacy_recovery_fiction(self):
        s=CORE.read_text()
        self.assertIn('NOT a recovery',s)
        self.assertIn('DISABLED_DEFAULT',s)

if __name__=='__main__':unittest.main()
