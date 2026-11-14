import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('lobby',ROOT/'apply_fb007_lobby.py')
lobby=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lobby)
GAME = '''local MapBuilder = require(script.Parent:WaitForChild("MapBuilder"))
local RunService=game:GetService("RunService")
local map = MapBuilder.build(Config)
local dojoPads={}
for _,side in ipairs({"RED","BLUE"}) do
 for _,kind in ipairs({"BEAST","WEAPON"}) do
  local pad=Instance.new("Part")
  pad.Position=Vector3.new(sign*56,-0.8,if kind=="BEAST" then -15 else 15)
 end
end
local match={phase="LOBBY"}
local function fakeDojo()
 if dt>0 and alive and root and pads
                    and match.phase~="RESULTS" and carry[player]==nil
                    and root.Position.Y>=-2 and root.Position.Y<=12 then
    Dojo.tick(state,kind,dt,dojoFriendHere(player),true)
 end
end
broadcast = function()
    for _,p in ipairs(Players:GetPlayers()) do
       remote:FireClient(p,snapshotFor(p))
    end
end
remote.Name = "TrapRaidersS1Remote"
remote.OnServerEvent:Connect(function(player,data) end)
local function assignSpawn(player: Player, character: Model)
 if root and root:IsA("BasePart") then
  if team=="RED" or team=="BLUE" then
     root.CFrame = map.teams[team].spawn + Vector3.new(0, 2, 0)
  end
 end
end
local function tickRound()
 if match.phase == "RESULTS" then
    if now >= match.phaseUntil then
            match.phase = "LOBBY"
            match.winner = ""
    end
 end
 for _, player in ipairs(Players:GetPlayers()) do
  if alive and root then
    if position.Y < -30 or math.abs(position.X) > 130
                or math.abs(position.Z) > 76 then
      if team == "RED" or team == "BLUE" then
        root.CFrame = map.teams[team].spawn + Vector3.new(0, 4, 0)
      end
    end
  end
 end
end
'''

class LobbyPhysicalTest(unittest.TestCase):
 def test_game_anchors_real_match_phase_authority(self):
  game=lobby.patch_game(GAME)
  self.assertIn('LobbyIsland.build(map.model)',game)
  self.assertIn('LobbyIsland.padPosition(side,kind)',game)
  self.assertIn('map.model:SetAttribute("P0D_PHASE",match.phase)',game)
  self.assertIn('match.phase=="LOBBY" and carry[player]==nil',game)
  self.assertIn('LobbyIsland.spawn(team)',game)
  self.assertIn('LobbyIsland.inLobby(position)',game)
  self.assertEqual(game.count('remote.OnServerEvent:Connect('),1)
  self.assertEqual(game.count('remote.Name = "TrapRaidersS1Remote"'),1)
  with self.assertRaises(AssertionError):lobby.patch_game(game)
 def test_author_v4_actual_source_unchanged_model_and_no_save(self):
  original=(ROOT/'overlays/V4TrainingBridge.server.luau').read_text('utf8')
  real=lobby.patch_v4(original)
  self.assertIn('LobbyIsland.padPosition(side,skill)',real)
  self.assertIn('LobbyIsland.padPosition(team,skill)',real)
  self.assertIn('if arena:GetAttribute("P0D_PHASE")~="LOBBY" then return nil end',real)
  self.assertNotIn('local positions = {',real)
  self.assertEqual(real.count('Scheduler.settle('),1)
  self.assertEqual(real.count('Model.apply('),1)
  self.assertIn('player:IsFriendsWithAsync(other.UserId)',real)
  with self.assertRaises(AssertionError):lobby.patch_v4(real)
 def build_fake(self,dist):
  v4=(ROOT/'overlays/V4TrainingBridge.server.luau').read_bytes()
  original={lobby.GAME:GAME.encode(),lobby.V4:v4}
  for i in range(64):original[f'server/immutable{i}.luau']=f'-- source {i}\n'.encode()
  for k,data in original.items():
   path=dist/'src'/k
   path.parent.mkdir(parents=True,exist_ok=True)
   path.write_bytes(data)
  lock={p:lobby.blob(b) for p,b in sorted(original.items())}
  (dist/'SOURCE_LOCK.json').write_text(json.dumps({'total_scripts':66,'blobs':lock}))
  (dist/'RC_FEATURE_LOCK.json').write_text(json.dumps({'total_sources':66,'source_gitblobs':lock,'feature_flags':{}}))
  (dist/'default.project.json').write_text(json.dumps({'tree':{'ServerScriptService':{'TrapRaidersS1':{'$path':'src/server'}}}}))
  return original
 def hashes(self,dist):
  return {p.relative_to(dist).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dist.rglob('*') if p.is_file()}
 def test_off_exact_and_on_only_two_scripts_one_module(self):
  with tempfile.TemporaryDirectory() as t:
   dist=Path(t);original=self.build_fake(dist)
   before=self.hashes(dist)
   self.assertFalse(lobby.apply(dist,False))
   self.assertEqual(before,self.hashes(dist))
   self.assertTrue(lobby.apply(dist,True))
   after=lobby.sources(dist)
   self.assertEqual(len(after),67)
   self.assertEqual({p for p in original if original[p]!=after[p]},{lobby.GAME,lobby.V4})
   self.assertTrue(all(original[p]==after[p] for p in original if p not in (lobby.GAME,lobby.V4)))
   self.assertEqual(lobby.blob(after[lobby.DEST]),lobby.MODULE_BLOB)
   self.assertEqual(json.loads((dist/'SOURCE_LOCK.json').read_text())['blobs'],
                    {p:lobby.blob(x) for p,x in sorted(after.items())})
 def test_source_lock_drift_rejects_before_writes(self):
  with tempfile.TemporaryDirectory() as t:
   dist=Path(t);self.build_fake(dist)
   (dist/'src'/lobby.GAME).write_text('wrong')
   with self.assertRaises(AssertionError):lobby.apply(dist,True)
   self.assertFalse((dist/'src'/lobby.DEST).exists())
 def test_real_lobby_module_is_physical_not_hidden_sign(self):
  s=lobby.MODULE.read_text('utf8')
  for token in ('LOBBY_SOLID_BASE','LOBBY_MEADOW','PAIRS = {','Lobby.padPosition',
                'Lobby.spawn','Lobby.inLobby','CanCollide = solid','P0D_SAFE_LOBBY',
                'BEAST','BUILDING','BEAST','Y + 5'):
   self.assertIn(token,s)
  for forbidden in ('RemoteEvent','TakeDamage(','UpdateAsync(','MarketplaceService'):
   self.assertNotIn(forbidden,s)

if __name__ == '__main__':
 unittest.main()
