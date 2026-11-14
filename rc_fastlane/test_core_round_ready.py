"""P0D candidate contract tests. Engine gameplay requires separate Studio QA."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('urgent', Path(__file__).with_name('apply_core_round_ready.py'))
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)

GAME = '''local Players = game:GetService("Players")
local roles: {[Player]: string} = {}
local lastSeq = {}
local remote = Instance.new("RemoteEvent")
remote.Name = "TrapRaidersS1Remote"
local match = {phase="LOBBY", phaseUntil=0}
local function snapshotFor(player)
 return {kind = "SNAPSHOT", serial = match.serial, phase = match.phase,}
end
local function stopRound()
    match.phase = "RESULTS"
end
local function onJoin(player)
    roles[player] = "RAIDER"
end
Players.PlayerRemoving:Connect(function(player)
    roles[player] = nil
end)
remote.OnServerEvent:Connect(function(player: Player, data)
    if type(data) ~= "table" then return end
    if data.action == "ATTACK" then applyAttack(player, data)
    end
end)
local function tickRound()
    if match.phase == "LOBBY" then
        rebalanceLobbyTeams()
        if count >= Config.MinPlayers then
            match.phase = "COUNTDOWN"
        end
    elseif match.phase == "COUNTDOWN" then
        if count < Config.MinPlayers then match.phase = "LOBBY" end
    elseif match.phase == "ACTIVE" then
        doCombat()
    end
end
'''
HUD = '''local gui = Instance.new("ScreenGui")
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote")
local seq = 0
local function action(kind, role)
 seq += 1
 remote:FireServer({action=kind,role=role,seq=seq})
end
attack.MouseButton1Click:Connect(function() action("ATTACK", nil) end)
local function phaseText(s): string
 return "ready"
end
remote.OnClientEvent:Connect(function(s)
    if s.kind ~= "SNAPSHOT" then return end
end)
'''
CONFIG = 'return {MinPlayers = 2, MatchSeconds = 360, CastleMaxHp = 300}\n'

class CoreRoundReadyTest(unittest.TestCase):
    def test_game_one_remote_and_server_only_ready(self):
        actual = u.patch_game(GAME)
        self.assertEqual(actual.count('remote.OnServerEvent:Connect('), 1)
        self.assertEqual(actual.count('remote.Name = "TrapRaidersS1Remote"'), 1)
        self.assertIn('if everybodyReady() and count >= Config.MinPlayers', actual)
        self.assertIn('if match.phase == "COUNTDOWN" and data.ready then return end', actual)
        self.assertIn('roundReady[player] = false', actual)
        self.assertIn('roundReady[player] = nil', actual)
        self.assertIn('ready = roundReady[player] == true', actual)
        self.assertEqual(actual.count('remote:FireClient'), 1)
        with self.assertRaises(AssertionError):
            u.patch_game(actual)

    def test_hud_button_hidden_in_active(self):
        actual = u.patch_hud(HUD)
        self.assertIn('readyButton.Visible = s.phase == "LOBBY" or s.phase == "COUNTDOWN"', actual)
        self.assertIn('ready=not isReady', actual)
        self.assertNotIn('readyButton.Visible = s.phase == "ACTIVE"', actual)

    def test_long_match_exact(self):
        actual = u.patch_config(CONFIG)
        self.assertIn('MatchSeconds = 900', actual)
        self.assertNotIn('MatchSeconds = 360', actual)
        with self.assertRaises(AssertionError):
            u.patch_config(actual)

    def test_drift_fails_closed(self):
        for fn, content in ((u.patch_game, GAME.replace('local roles:', 'local jobs:')),
                            (u.patch_hud, HUD.replace('local seq = 0', 'local id = 0')),
                            (u.patch_config, CONFIG.replace('360', '600'))):
            with self.assertRaises(AssertionError):
                fn(content)

    def test_candidate_all_bytes_off_and_three_changed_on(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            fake = {
                'server/Game.server.luau': GAME.encode(),
                'client/HUD.client.luau': HUD.encode(),
                'shared/Config.luau': CONFIG.encode(),
            }
            # Real RC66 is enforced by contract, not simulated as 66 valuable scripts.
            for i in range(63):
                fake[f'client/unchanged{i}.luau'] = f'-- source {i}\n'.encode()
            for path, value in fake.items():
                p=dist/'src'/path
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(value)
            pins = {p:u.gitblob(b) for p,b in sorted(fake.items())}
            (dist/'SOURCE_LOCK.json').write_text(json.dumps({'total_scripts':66,'blobs':pins}))
            (dist/'RC_FEATURE_LOCK.json').write_text(json.dumps({'total_sources':66,'source_gitblobs':pins,'feature_flags':{}}))
            before={p.relative_to(dist).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dist.rglob('*') if p.is_file()}
            self.assertFalse(u.apply(dist,False))
            off={p.relative_to(dist).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dist.rglob('*') if p.is_file()}
            self.assertEqual(before,off)
            self.assertTrue(u.apply(dist,True))
            src=u.sources(dist)
            self.assertEqual(len(src),66)
            self.assertEqual({p for p in fake if fake[p]!=src[p]},u.TARGET)
            self.assertEqual(json.loads((dist/'SOURCE_LOCK.json').read_text())['blobs'],
                             {p:u.gitblob(v) for p,v in sorted(src.items())})

if __name__ == '__main__': unittest.main()
