"""Actual source-locked Python proof for S1 lobby deadlock full-source patch.

Runs only after actions/checkout@v4 has checked out:
- own branch with the complete Game source candidate at c609...
- immutable_baseline at 35d7...
- previous_patch at 7693...

Source-only; native Luau and Roblox Studio 2-client are NOT tested.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
BASE_SHA = 'd7abfc3b6ae1412cad995873faec1c5e4a1a9df1c0971991cff919564a628f3f'
PATCH_SHA = '7b19a98826add9c6555f8da3d42b5dc046676caeb849e0c796c727093e57f977'
PLANNER_SHA = '35c546f33e0454ceaf7fa26cf5ee44763673c6764906cc249ef282bb096ea404'
BASE_BLOB = '0f2c34fe25c00e3251b9ca53952b9ec75400f365'
PLANNER_BLOB = 'db1a369133550bc8356a4ee3ac22b97fcb1b46c4'
PATCH_BLOB = 'cecfc735af1343dbec9aea6920934fa2c995677f'
BASE = REPO / 'immutable_baseline/releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau'
PACK = REPO / 'handoffs/P0D-S1-LOBBY-TEAM-DEADLOCK-FULL-GAME-20261111-02'
PATCHED = PACK / 'src/server/Game.server.luau'
PLANNER = PACK / 'src/server/LobbyTeamRecovery.luau'
PREVIOUS_PLANNER = REPO / 'previous_patch/handoffs/P0D-S1-LOBBY-TEAM-DEADLOCK-RECOVERY-20261111-01/src/LobbyTeamRecovery.luau'
SELF_ROOT = Path(__file__).resolve().parents[1]


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def gitblob(b: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(b)).encode('ascii') + b'\0' + b).hexdigest()


def get_src(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f'SOURCE_NOT_PRESENT: {path}')
    return path.read_bytes()


def differences() -> list[tuple[str, str, str]]:
    before = get_src(BASE).decode('utf-8').splitlines(keepends=True)
    after = get_src(PATCHED).decode('utf-8').splitlines(keepends=True)
    result = []
    for op, i, j, k, l in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes():
        if op != 'equal':
            result.append((op, ''.join(before[i:j]), ''.join(after[k:l])))
    return result


class ExactFullSource(unittest.TestCase):
    def test_expected_baseline_sha256_and_size(self):
        b = get_src(BASE)
        self.assertEqual(digest(b), BASE_SHA)
        self.assertEqual(len(b), 16860)
        self.assertEqual(gitblob(b), BASE_BLOB)

    def test_expected_patched_sha256_and_size(self):
        b = get_src(PATCHED)
        self.assertEqual(digest(b), PATCH_SHA)
        self.assertEqual(len(b), 18324)
        self.assertEqual(gitblob(b), PATCH_BLOB)

    def test_planner_is_bit_identical_previous(self):
        b = get_src(PLANNER)
        self.assertEqual(b, get_src(PREVIOUS_PLANNER))
        self.assertEqual(digest(b), PLANNER_SHA)
        self.assertEqual(gitblob(b), PLANNER_BLOB)

    def test_exactly_four_disjoint_source_changes(self):
        diffs = differences()
        self.assertEqual(len(diffs), 4, diffs)
        self.assertEqual([d[0] for d in diffs], ['insert', 'insert', 'insert', 'replace'])
        self.assertEqual(diffs[0][1], '')
        self.assertEqual(diffs[0][2].strip(), 'local LobbyTeamRecovery = require(script.Parent:WaitForChild("LobbyTeamRecovery"))')
        self.assertEqual(diffs[1][1], '')
        self.assertIn('local function rebalanceLobbyTeams()', diffs[1][2])
        self.assertIn('if match.phase ~= "LOBBY" then return end', diffs[1][2])
        self.assertIn('LobbyTeamRecovery.plan(roster)', diffs[1][2])
        self.assertEqual(diffs[2][1], '')
        self.assertEqual(diffs[2][2].strip(), 'rebalanceLobbyTeams()')
        self.assertEqual(diffs[3][1].strip(), 'if count < Config.MinPlayers then match.phase = "LOBBY"\n        elseif now >= match.phaseUntil then resetRound() end')
        self.assertIn('teamCount("RED") == 0 or teamCount("BLUE") == 0', diffs[3][2])
        self.assertIn('match.phase = "LOBBY"', diffs[3][2])

    def test_round_authority_and_rules_preserved(self):
        before = get_src(BASE).decode()
        after = get_src(PATCHED).decode()
        shared = ('local match = {', 'Instance.new("RemoteEvent")', 'local function snapshotFor(player: Player)',
                  'local function stopRound(winner: string, reason: string)', 'local function resetRound()',
                  'local function applyAttack(player: Player, data)', 'local function applyRole(player: Player, data)',
                  'local function tickRound()', 'remote.OnServerEvent:Connect',
                  'match.scores[team] += 1', 'hum:TakeDamage(',
                  'task.spawn(function()\n    while true do\n        tickRound()')
        for marker in shared:
            with self.subTest(marker=marker):
                self.assertEqual(before.count(marker), 1)
                self.assertEqual(after.count(marker), 1)
        self.assertEqual(after.count('local function rebalanceLobbyTeams()'), 1)
        self.assertEqual(after.count('        rebalanceLobbyTeams()'), 1)

    def test_planner_not_second_authority(self):
        src = get_src(PLANNER).decode()
        for forbidden in ('RemoteEvent', 'FireServer', 'OnServerEvent', 'DataStore', 'TakeDamage(', 'LoadCharacter(', 'task.spawn('):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, src)
        self.assertIn('function LobbyTeamRecovery.plan(roster: any)', src)

    def test_negative_tampering_rejected_by_sha(self):
        b = get_src(PATCHED)
        self.assertEqual(digest(b), PATCH_SHA)
        bad = b.replace(b'LobbyTeamRecovery.plan(roster)', b'LobbyTeamRecovery.plan({})', 1)
        self.assertNotEqual(b, bad)
        self.assertNotEqual(digest(bad), PATCH_SHA)
        self.assertNotEqual(gitblob(bad), PATCH_BLOB)

    def test_fail_closed_unknown_baseline(self):
        b = get_src(BASE)
        bad = b.replace(b'if match.phase == "LOBBY"', b'if match.phase == "ACTIVE"', 1)
        self.assertNotEqual(b, bad)
        self.assertNotEqual(digest(bad), BASE_SHA)
        self.assertNotEqual(gitblob(bad), BASE_BLOB)

    def test_original_v1_manifest_and_own_ci_manifest(self):
        for folder, count in ((PACK, 6), (SELF_ROOT, 4)):
            with self.subTest(folder=str(folder)):
                manifest = json.loads((folder / 'BUILD_MANIFEST.json').read_text(encoding='utf8'))
                self.assertEqual(set(manifest), {'format','game_id','work_id','packet_id','public_source_allowed','files'})
                self.assertEqual(manifest['format'], 'P0D_PUBLIC_SOURCE_V1')
                self.assertEqual(manifest['game_id'], 'TRAP_RAIDERS')
                self.assertEqual(manifest['work_id'], 'p0d-siege-v19')
                self.assertIs(manifest['public_source_allowed'], True)
                self.assertEqual(len(manifest['files']), count)
                for entry in manifest['files']:
                    fp = (folder / entry['path']).resolve()
                    self.assertTrue(fp.is_relative_to(folder.resolve()))
                    bb = fp.read_bytes()
                    self.assertEqual(len(bb), entry['size'])
                    self.assertEqual(digest(bb), entry['sha256'])


if __name__ == '__main__':
    unittest.main()
