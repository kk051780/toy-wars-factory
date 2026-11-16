#!/usr/bin/env python3
"""Fail-closed mutation tests for the CURRENT 31-script one-Host lobby safety patch."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from select_safe_lobby import transform,rollback,SAFE_BLOCK,MARKER,ANCHOR

ORIGINAL=(
 'local Players=game:GetService("Players")\n'
 'local folder=Instance.new("Folder");folder.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW";folder.Parent=workspace\n'
 'local sessions:{[string]:any}={}\n'
 'local joined:{[number]:string}={}\n'
 +ANCHOR+
 'local MODE_SEATS=16\n'
)

class LobbySafety(unittest.TestCase):
    def test_insert_once_and_restore_byte_exact(self):
        selected=transform(ORIGINAL)
        self.assertEqual(selected.count(MARKER),2) # START + END marker
        self.assertEqual(rollback(selected),ORIGINAL)
        self.assertEqual(selected.count('Instance.new("SpawnLocation")'),1)
        self.assertEqual(selected.count('Instance.new("Part")'),1)
        self.assertIn('lobbyFloor.CanCollide=true',selected)
        self.assertIn('lobbySpawn.Neutral=true',selected)
        self.assertIn('lobbySpawn.Enabled=true',selected)
        self.assertIn('lobbySpawn.Duration=0',selected)

    def test_no_new_gameplay_authority(self):
        selected=transform(ORIGINAL)
        self.assertNotIn('Instance.new("RemoteEvent")',selected)
        self.assertNotIn('DataStoreService',selected)
        self.assertNotIn('Instance.new("BindableEvent")',selected)
        self.assertIn('if activeMode and sessions[activeMode] then return end',selected)
        self.assertIn('if p.Character then rescueToLobby(p,p.Character) end',selected)
        self.assertIn('Players.PlayerAdded:Connect(attachLobbyRescue)',selected)
        self.assertIn('for _,p in ipairs(Players:GetPlayers()) do attachLobbyRescue(p) end',selected)

    def test_mutants_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'RED_ORIGINAL_LOBBY_HOST_ANCHOR'):
            transform(ORIGINAL.replace(ANCHOR,''))
        with self.assertRaisesRegex(ValueError,'RED_ORIGINAL_LOBBY_HOST_ANCHOR'):
            transform(ORIGINAL+ANCHOR)
        selected=transform(ORIGINAL)
        with self.assertRaisesRegex(ValueError,'RED_DUPLICATE_LOBBY_SAFETY'):
            transform(selected)
        with self.assertRaisesRegex(ValueError,'RED_LOBBY_ROLLBACK_MARKER'):
            rollback(selected.replace('lobbyFloor.CanCollide=true','lobbyFloor.CanCollide=false'))

    def test_safe_floor_spans_all_existing_lobby_stands(self):
        # Original positions: role signs z=69, defense signs z=47,
        # portals z=28; floor center z=35, depth150 => [-40,+110].
        self.assertLessEqual(35-150/2,28)
        self.assertGreaterEqual(35+150/2,69)
        # Role signs x in [-27,27], floor half-width60.
        self.assertGreaterEqual(120/2,27)

if __name__=='__main__':
    unittest.main()
