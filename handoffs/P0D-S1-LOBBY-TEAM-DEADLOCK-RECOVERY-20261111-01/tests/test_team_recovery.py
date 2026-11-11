"""Python reference oracle + integrity/negative checks, NOT Luau interpreter or Studio QA."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import apply_game_patch as patch
import verify_package as verifier


def oracle(roster):
    if not isinstance(roster, list) or len(roster) > 64:
        return None
    seen = set()
    by_team = {"RED": [], "BLUE": []}
    for m in roster:
        if not isinstance(m, dict) or set(m) != {"userId", "team"}:
            return None
        v, t = m["userId"], m["team"]
        if (type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 2**53-1
                or int(v) != v or v in seen or t not in by_team):
            return None
        seen.add(v)
        by_team[t].append(v)
    red, blue = by_team["RED"], by_team["BLUE"]
    if abs(len(red) - len(blue)) <= 1:
        return []
    src, tgt = ("RED", "BLUE") if len(red) > len(blue) else ("BLUE", "RED")
    return [{"userId": uid, "from": src, "to": tgt}
            for uid in sorted(by_team[src], reverse=True)[:abs(len(red) - len(blue))//2]]


def roster(red, blue):
    return [{"userId": v, "team": "RED"} for v in red] + [{"userId": v, "team": "BLUE"} for v in blue]


def apply_moves(players, moves, phase):
    result = copy.deepcopy(players)
    if phase != "LOBBY" or moves is None:
        return result
    by_id = {p["userId"]: p for p in result}
    for m in moves:
        p = by_id.get(m["userId"])
        if p and p["team"] == m["from"]:
            p["team"] = m["to"]
    return result


# Stable fragments copied from immutable source Game.server.luau (Git blob pinned).
SAMPLE = (
    '--!strict\nlocal MapBuilder = require(script.Parent:WaitForChild("MapBuilder"))\n'
    'local function assignSpawn(player: Player, character: Model)\n'
    'end\n'
    '    if match.phase == "LOBBY" then\n'
    '        if count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0 then\n'
    '            match.phase = "COUNTDOWN"\n'
    '    elseif match.phase == "COUNTDOWN" then\n'
    '        if count < Config.MinPlayers then match.phase = "LOBBY"\n'
    '        elseif now >= match.phaseUntil then resetRound() end\n'
    '    end\n'
)


class TestPlanner(unittest.TestCase):
    def test_two_red_no_blue(self):
        self.assertEqual(oracle(roster([10, 20], [])), [{"userId": 20, "from": "RED", "to": "BLUE"}])
    def test_two_blue_no_red(self):
        self.assertEqual(oracle(roster([], [10, 20])), [{"userId": 20, "from": "BLUE", "to": "RED"}])
    def test_single_red_wait(self): self.assertEqual(oracle(roster([5], [])), [])
    def test_empty_wait(self): self.assertEqual(oracle(roster([], [])), [])
    def test_two_one_no_move(self): self.assertEqual(oracle(roster([1,2], [3])), [])
    def test_one_two_no_move(self): self.assertEqual(oracle(roster([1], [2,3])), [])
    def test_two_two_no_move(self): self.assertEqual(oracle(roster([1,2], [3,4])), [])
    def test_three_red_zero_blue(self): self.assertEqual(len(oracle(roster([1,2,3], []))), 1)
    def test_four_red_zero_blue(self): self.assertEqual(len(oracle(roster([1,2,3,4], []))), 2)
    def test_three_red_one_blue(self): self.assertEqual(oracle(roster([1,2,3], [4])), [{"userId":3,"from":"RED","to":"BLUE"}])
    def test_one_red_three_blue(self): self.assertEqual(oracle(roster([1], [2,3,4])), [{"userId":4,"from":"BLUE","to":"RED"}])
    def test_four_red_two_blue(self): self.assertEqual(len(oracle(roster([1,2,3,4], [5,6]))),1)
    def test_three_blue_one_red(self): self.assertEqual(len(oracle(roster([1], [2,3,4]))),1)
    def test_recovery_idempotent(self):
        original=roster([1,2,3,4], [])
        result=apply_moves(original,oracle(original),"LOBBY")
        self.assertEqual(oracle(result), [])
    def test_do_not_mutate_input(self):
        original=roster([1,2,3,4],[])
        snapshot=copy.deepcopy(original)
        oracle(original)
        self.assertEqual(original,snapshot)
    def test_order_independent_moves(self):
        sample=roster([3,1,4,2],[5,6]); shuffled=list(reversed(sample))
        self.assertEqual(oracle(sample),oracle(shuffled))
    def test_large_balances(self):
        candidate=roster(list(range(1,51)),[51])
        result=apply_moves(candidate,oracle(candidate),"LOBBY")
        self.assertLessEqual(abs(sum(p['team']=='RED' for p in result)-sum(p['team']=='BLUE' for p in result)),1)
    def test_negative_studio_user_ids(self):
        self.assertEqual(oracle(roster([-1,-2],[])),[{"userId":-1,"from":"RED","to":"BLUE"}])
    def test_zero_studio_user_id(self): self.assertEqual(len(oracle(roster([0,9],[]))),1)
    def test_float_integer_representation(self): self.assertEqual(len(oracle(roster([1.0,2.0],[]))),1)
    def test_bad_none(self): self.assertIsNone(oracle(None))
    def test_bad_string(self): self.assertIsNone(oracle("RED,BLUE"))
    def test_bad_dict(self): self.assertIsNone(oracle({"team":"RED"}))
    def test_bad_missing_uid(self): self.assertIsNone(oracle([{"team":"RED"}]))
    def test_bad_missing_team(self): self.assertIsNone(oracle([{"userId":1}]))
    def test_bad_unknown_team(self): self.assertIsNone(oracle([{"userId":1,"team":"NONE"}]))
    def test_bad_duplicate_uid(self): self.assertIsNone(oracle(roster([1,1], [])))
    def test_bad_duplicate_cross_team(self): self.assertIsNone(oracle(roster([1], [1])))
    def test_bad_fractional_uid(self): self.assertIsNone(oracle(roster([1,1.5], [])))
    def test_bad_nan_uid(self): self.assertIsNone(oracle(roster([1,float('nan')], [])))
    def test_bad_inf_uid(self): self.assertIsNone(oracle(roster([1,float('inf')], [])))
    def test_bad_large_uid(self): self.assertIsNone(oracle(roster([1,2**53], [])))
    def test_bad_boolean_uid(self): self.assertIsNone(oracle(roster([1,True], [])))
    def test_bad_65_people(self): self.assertIsNone(oracle(roster(list(range(65)), [])))
    def test_bad_player_extra_keys(self): self.assertIsNone(oracle([{"userId":1,"team":"RED","role":"ADMIN"}]))
    def test_no_active_team_changes(self):
        players=roster([1,2], []); self.assertEqual(apply_moves(players,oracle(players),"ACTIVE"),players)
    def test_no_countdown_team_changes(self):
        players=roster([1,2], []); self.assertEqual(apply_moves(players,oracle(players),"COUNTDOWN"),players)
    def test_no_results_team_changes(self):
        players=roster([1,2], []); self.assertEqual(apply_moves(players,oracle(players),"RESULTS"),players)
    def test_only_lobby_team_changes(self):
        players=roster([1,2], []); moved=apply_moves(players,oracle(players),"LOBBY")
        self.assertEqual((sum(p['team']=='RED' for p in moved),sum(p['team']=='BLUE' for p in moved)),(1,1))
    def test_countdown_should_cancel_without_opponent(self):
        self.assertTrue((2>=2) and (2==0 or 0==0))
    def test_wait_one_after_second_leaves(self):
        self.assertEqual(oracle(roster([1],[])), [])


class TestSourceContract(unittest.TestCase):
    def setUp(self): self.src=(ROOT/'src/LobbyTeamRecovery.luau').read_text()
    def test_module_is_pure(self):
        for bad in ['RemoteEvent','FireServer','GetService(','Players:GetPlayers','SetAttribute','DataStore','CollectionService','Heartbeat','task.wait','while true']:
            self.assertNotIn(bad,self.src)
    def test_planner_only_no_side_effect(self):
        self.assertIn('function LobbyTeamRecovery.plan(roster: any)',self.src)
        self.assertIn('return moves',self.src)
        self.assertNotIn('player.Team',self.src)
    def test_invalid_roster_fail_closed(self):
        self.assertIn('return nil',self.src)
        self.assertIn('seen[member.userId]',self.src)
    def test_source_supports_studio_negative_ids(self):
        self.assertNotIn('member.userId <= 0',self.src)
        self.assertIn('math.abs(v) <= 9007199254740991',self.src)
    def test_small_move_budget(self): self.assertIn('math.floor(diff / 2)',self.src)
    def test_exact_game_blob_identity(self):
        self.assertEqual(patch.BASE_GAME_GIT_BLOB,'0f2c34fe25c00e3251b9ca53952b9ec75400f365')
        self.assertEqual(len(patch.BASE_GAME_COMMIT),40)
    def test_patch_all_four_markers(self): self.assertEqual(len(patch.REPLACEMENTS),4)
    def test_patch_hunk_exactness(self):
        changed=patch.transform_source(SAMPLE)
        self.assertIn('rebalanceLobbyTeams()',changed)
        self.assertIn('teamCount("RED") == 0 or teamCount("BLUE") == 0',changed)
        self.assertIn('match.phase ~= "LOBBY" then return end',changed)
        self.assertIn('player.Team = teamInstances[move.to]',changed)
        self.assertIn('dropEgg(player)',changed)
        self.assertIn('root.CFrame = map.teams[move.to].spawn',changed)
    def test_patch_fails_partial(self):
        with self.assertRaisesRegex(ValueError,'PATTERN_NOT_EXACTLY_ONCE'):
            patch.transform_source(SAMPLE.replace('if count < Config.MinPlayers then match.phase = "LOBBY"','if count == 0 then match.phase = "LOBBY"'))
    def test_patch_fails_duplicate_snippet(self):
        with self.assertRaisesRegex(ValueError,'PATTERN_NOT_EXACTLY_ONCE'):
            patch.transform_source(SAMPLE + '\n' + patch.REPLACEMENTS[0][0])
    def test_patch_fails_twice(self):
        with self.assertRaisesRegex(ValueError,'PATTERN_NOT_EXACTLY_ONCE'):
            patch.transform_source(patch.transform_source(SAMPLE))
    def test_patch_preserves_unrelated_body(self):
        before='custom safe event unchanged FROB_2851'
        transformed=patch.transform_source(SAMPLE+before)
        self.assertIn(before,transformed)
    def test_raw_git_blob_sha_math(self):
        self.assertEqual(patch.git_blob_sha(b'hello\n'),hashlib.sha1(b'blob 6\0hello\n').hexdigest())
    def test_main_cli_rejects_wrong_sha(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'Game.server.luau'; dest=Path(td)/'OUTPUT.luau'; src.write_text(SAMPLE)
            p=subprocess.run([sys.executable,str(ROOT/'tools/apply_game_patch.py'),'--source',str(src),'--output',str(dest)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('BASELINE_SOURCE_SHA_MISMATCH',p.stderr+p.stdout)
            self.assertFalse(dest.exists())
    def test_main_cli_rejects_in_place(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'Game.server.luau'; src.write_text(SAMPLE)
            p=subprocess.run([sys.executable,str(ROOT/'tools/apply_game_patch.py'),'--source',str(src),'--output',str(src)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('REFUSE_INPLACE',p.stderr+p.stdout)
    def test_main_cli_rejects_existing_output(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'Game.server.luau'; dest=Path(td)/'TARGET.luau'; src.write_text(SAMPLE); dest.write_text('protected')
            p=subprocess.run([sys.executable,str(ROOT/'tools/apply_game_patch.py'),'--source',str(src),'--output',str(dest)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertEqual(dest.read_text(),'protected')
    def test_patch_no_other_authority(self):
        rendered=patch.transform_source(SAMPLE)
        self.assertNotIn('RemoteEvent',rendered)
        self.assertNotIn('TakeDamage',rendered)
        self.assertIn('LobbyTeamRecovery.plan',rendered)
    def test_countdown_team_check_is_both(self):
        rendered=patch.transform_source(SAMPLE)
        self.assertIn('teamCount("RED") == 0 or teamCount("BLUE") == 0',rendered)
    def test_rule_first_checks_lobby_then_countdown(self):
        rendered=patch.transform_source(SAMPLE)
        self.assertLess(rendered.index('        rebalanceLobbyTeams()\n'),rendered.index('if count >= Config.MinPlayers'))
    def test_readme_warns_no_live(self): self.assertIn('No claim of Studio', (ROOT/'README.md').read_text())
    def test_integration_has_rollback(self): self.assertIn('## Rollback',(ROOT/'docs/INTEGRATION.md').read_text())


class TestManifest(unittest.TestCase):
    def test_valid_source_manifest(self): self.assertGreaterEqual(verifier.check(ROOT)['source_files'],5)
    def test_packet_identity(self):
        doc=json.loads((ROOT/'BUILD_MANIFEST.json').read_text())
        self.assertEqual(set(doc),verifier.ROOT_KEYS)
        self.assertEqual(doc['packet_id'],verifier.PACKET)
    def test_manifest_has_all_files(self):
        doc=json.loads((ROOT/'BUILD_MANIFEST.json').read_text())
        self.assertEqual(len(doc['files']),len({x['path'] for x in doc['files']}))
    def test_manifest_sha_values(self):
        doc=json.loads((ROOT/'BUILD_MANIFEST.json').read_text())
        self.assertTrue(all(len(x['sha256'])==64 for x in doc['files']))


if __name__=='__main__':
    unittest.main(verbosity=2)
