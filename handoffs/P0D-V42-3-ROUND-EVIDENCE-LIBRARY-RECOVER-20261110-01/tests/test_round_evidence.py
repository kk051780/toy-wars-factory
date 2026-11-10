import copy
import json
import pathlib
import random
import unittest
from round_evidence_reference import derive, JOBS, ACTIONS, ASSISTS

BASE = pathlib.Path(__file__).resolve().parents[1]
GOLDEN = json.loads((BASE/'fixtures'/'golden_rounds.json').read_text(encoding='utf-8'))

class RoundGateTests(unittest.TestCase):
    def setUp(self):
        self.round = copy.deepcopy(GOLDEN['baseline']['round'])
        self.player = copy.deepcopy(GOLDEN['baseline']['player'])

    def call(self, rid=101):
        return derive(self.round, self.player, rid)

    def test_valid_winning_receipt(self):
        result,error=self.call()
        self.assertIsNone(error)
        self.assertTrue(result['won'])
        self.assertTrue(result['eggDelivered'])
        self.assertEqual(result['assistKinds'],['defense','rescue','siege'])
        self.assertEqual(result['meaningfulActionCount'],3)

    def test_valid_loser(self):
        self.round['eggDeliveredByUserId']=102
        self.round['participantTeams']={'101':'RED','102':'BLUE'}
        self.player['team']='RED'
        result,error=self.call()
        self.assertIsNone(error)
        self.assertFalse(result['won'])
        self.assertFalse(result['eggDelivered'])

    def test_draw(self):
        self.round.update(winnerTeam='DRAW',eggDeliveredByUserId=None,eggDeliveredByTeam=None)
        result,error=self.call()
        self.assertIsNone(error)
        self.assertFalse(result['won'])

    def test_immaterial_afk_is_passed_to_core_not_rewarded_here(self):
        self.player['activeSeconds']=0
        self.player['actionCounts']={key:0 for key in ACTIONS}
        result,error=self.call()
        self.assertIsNone(error)
        self.assertEqual(result['meaningfulActionCount'],0)
        self.assertEqual(result['participationSeconds'],0)
        # The progression core must reject AFK. Gate must never mint XP itself.
        self.assertNotIn('earnedXp',result)

    def test_all_seven_jobs(self):
        for job in JOBS:
            with self.subTest(job=job):
                self.player['job']=job
                self.assertIsNone(self.call()[1])

    def test_all_four_maps(self):
        for stage in ['S1','S2','S3','S4']:
            with self.subTest(stage=stage):
                self.round['mapId']=stage
                self.assertIsNone(self.call()[1])

    def test_input_unchanged(self):
        r,p=copy.deepcopy(self.round),copy.deepcopy(self.player)
        self.call()
        self.assertEqual((r,p),(self.round,self.player))

    def test_throws_no_unexpected_truthy_client_flags(self):
        self.player['assistFlags']['rescue']='true'
        self.assertEqual(self.call()[1],'INVALID_ASSIST_FLAGS')

    def test_reject_lifecycle(self):
        for value in [None,'RUNNING','RESULT_PENDING','REPLAY']:
            with self.subTest(value=value):
                self.round['phase']=value
                self.assertEqual(self.call()[1],'ROUND_NOT_FINALIZED')
        self.round['phase']='RESULT_FINALIZED'
        self.round['serverOwned']='true'
        self.assertEqual(self.call()[1],'ROUND_NOT_FINALIZED')

    def test_reject_bad_match_ids(self):
        for value in ['../../etc/passwd','short','abc defghi','🍀'*10, '',None, 'a'*81]:
            with self.subTest(value=value):
                self.round['matchId']=value
                self.assertEqual(self.call()[1],'INVALID_MATCH_ID')

    def test_reject_bad_winner_or_map(self):
        self.round['winnerTeam']='GREEN'
        self.assertEqual(self.call()[1],'INVALID_WINNER')
        self.round['winnerTeam']='BLUE'
        self.round['mapId']='S5'
        self.assertEqual(self.call()[1],'INVALID_MAP')

    def test_roster_claims_rejected(self):
        self.player['team']='RED'
        self.assertEqual(self.call()[1],'ROSTER_TEAM_MISMATCH')
        self.player['team']='BLUE'
        self.round['participantTeams']['102']='UNKNOWN'
        self.assertEqual(self.call()[1],'ROSTER_TEAM_MISMATCH')

    def test_egg_carrier_team_must_match_winner(self):
        self.round['eggDeliveredByUserId']=102
        self.assertEqual(self.call()[1],'INVALID_EGG_RECEIPT')

    def test_no_trust_claims_minted_by_shape_check(self):
        result,error=self.call()
        self.assertIsNone(error)
        self.assertNotIn('serverValidated',result)
        self.assertNotIn('isCurrentActiveMatch',result)

    def test_reject_unknown_job_and_team(self):
        self.player['job']='PAY_TO_WIN'
        self.assertEqual(self.call()[1],'INVALID_JOB')
        self.player['job']='TRAPPER'
        self.player['team']='NONE'
        self.assertEqual(self.call()[1],'INVALID_TEAM')

    def test_reject_invalid_snapshot(self):
        self.assertEqual(derive(None,self.player,101)[1],'INVALID_SNAPSHOT')
        self.assertEqual(derive(self.round,[],101)[1],'INVALID_SNAPSHOT')

    def test_reject_mismatched_user_and_membership(self):
        self.player['userId']=102
        self.assertEqual(self.call()[1],'PARTICIPANT_MISMATCH')
        self.player['userId']=101
        self.round['participantUserIds']=[102]
        self.assertEqual(self.call()[1],'PARTICIPANT_MISMATCH')

    def test_reject_duplicate_member_and_late_invalid_member(self):
        self.round['participantUserIds']=[101,101]
        self.assertEqual(self.call()[1],'PARTICIPANT_MISMATCH')
        self.round['participantUserIds']=[101,'BOGUS']
        self.assertEqual(self.call()[1],'PARTICIPANT_MISMATCH')

    def test_reject_bad_user_id(self):
        for value in [True,0,-1,1.1,float('inf'),'101']:
            with self.subTest(value=value):
                self.assertEqual(self.call(value)[1],'PARTICIPANT_MISMATCH')

    def test_reject_bad_duration(self):
        for value in [0,-1,3601,float('nan'),'60',float('inf')]:
            with self.subTest(value=str(value)):
                self.round['durationSeconds']=value
                self.assertEqual(self.call()[1],'INVALID_DURATION')

    def test_reject_bad_active_time(self):
        for value in [-1,61,'30',float('nan'),float('inf')]:
            with self.subTest(value=str(value)):
                self.player['activeSeconds']=value
                self.assertEqual(self.call()[1],'INVALID_ACTIVE_TIME')

    def test_reject_bad_counters(self):
        for value in [-1,1.1,'1',True,float('nan'),float('inf'),100001]:
            with self.subTest(value=str(value)):
                self.player['actionCounts']['enemyHits']=value
                self.assertEqual(self.call()[1],'INVALID_ACTION_COUNTS')

    def test_requires_every_action_counter(self):
        for key in ACTIONS:
            with self.subTest(key=key):
                counts=copy.deepcopy(self.player['actionCounts'])
                del counts[key]
                self.player['actionCounts']=counts
                self.assertEqual(self.call()[1],'INVALID_ACTION_COUNTS')
                self.player['actionCounts']=copy.deepcopy(GOLDEN['baseline']['player']['actionCounts'])

    def test_requires_every_assist_flag(self):
        for key in ASSISTS:
            with self.subTest(key=key):
                flags=copy.deepcopy(self.player['assistFlags'])
                del flags[key]
                self.player['assistFlags']=flags
                self.assertEqual(self.call()[1],'INVALID_ASSIST_FLAGS')
                self.player['assistFlags']=copy.deepcopy(GOLDEN['baseline']['player']['assistFlags'])

    def test_unlinked_egg_receipt_rejected(self):
        self.round['eggDeliveredByTeam']=None
        self.assertEqual(self.call()[1],'INVALID_EGG_RECEIPT')
        self.round['eggDeliveredByTeam']='BLUE'
        self.round['eggDeliveredByUserId']=999
        self.assertEqual(self.call()[1],'INVALID_EGG_RECEIPT')

    def test_egg_team_conflict_rejected(self):
        self.round['eggDeliveredByTeam']='RED'
        self.assertEqual(self.call()[1],'INVALID_EGG_RECEIPT')

    def test_egg_does_not_depend_on_player_claim(self):
        self.player['eggDelivered']=True
        self.round['eggDeliveredByUserId']=None
        self.round['eggDeliveredByTeam']=None
        result,error=self.call()
        self.assertIsNone(error)
        self.assertFalse(result['eggDelivered'])

    def test_player_client_claims_not_read(self):
        self.player['won']=True
        self.player['earnedXp']=999999
        self.player['serverValidated']=True
        result,error=self.call()
        self.assertIsNone(error)
        self.assertNotIn('earnedXp',result)
        self.assertEqual(result['won'], True)  # from server round, not player claims

    def test_server_snapshot_ignores_client_extra_abilities(self):
        self.player['permanentAtkBonus']=100000
        self.player['bossControlSeconds']=100000
        result,error=self.call()
        self.assertIsNone(error)
        self.assertFalse(any(x in result for x in ('permanentAtkBonus','bossControlSeconds')))

    def test_output_not_aliasing_mutable_input(self):
        result,error=self.call()
        self.assertIsNone(error)
        self.player['assistFlags']['defense']=False
        self.round['matchId']='NEW_ID_12345'
        self.assertEqual(result['assistKinds'],['defense','rescue','siege'])
        self.assertEqual(result['matchId'],GOLDEN['baseline']['round']['matchId'])

    def test_no_reward_calculation_in_gate(self):
        output,error=self.call()
        self.assertIsNone(error)
        self.assertNotIn('xp', output)
        self.assertNotIn('level', output)

    def test_golden_cases(self):
        for name,case in GOLDEN['cases'].items():
            with self.subTest(case=name):
                round_=copy.deepcopy(GOLDEN['baseline']['round'])
                player=copy.deepcopy(GOLDEN['baseline']['player'])
                round_.update(case.get('round',{}))
                player.update(case.get('player',{}))
                result,error=derive(round_,player,case.get('expectedUserId',101))
                self.assertEqual(error,case.get('error'))
                if result and 'won' in case:
                    self.assertEqual(result['won'],case['won'])
                if result and 'eggDelivered' in case:
                    self.assertEqual(result['eggDelivered'],case['eggDelivered'])

    def test_fuzz_rejects_nonfinite_counters(self):
        rng=random.Random(42003)
        bad=[-1,1.5,100001,True,'8',None,float('nan'),float('inf'),-float('inf')]
        for _ in range(2000):
            self.player['actionCounts'][rng.choice(ACTIONS)]=rng.choice(bad)
            _,error=self.call()
            self.assertEqual(error,'INVALID_ACTION_COUNTS')
            self.player['actionCounts']=copy.deepcopy(GOLDEN['baseline']['player']['actionCounts'])

    def test_fuzz_valid_counters_never_yield_xp(self):
        rng=random.Random(42004)
        for _ in range(2000):
            self.player['actionCounts']={k:rng.randrange(0,999) for k in ACTIONS}
            result,error=self.call()
            self.assertIsNone(error)
            self.assertEqual(result['meaningfulActionCount'],sum(self.player['actionCounts'].values()))
            self.assertNotIn('earnedXp',result)

    def test_no_client_remote_or_store_api_in_reference_source(self):
        luau=(BASE/'luau'/'RoundEvidenceGate.luau').read_text(encoding='utf-8')
        for term in ('OnServerEvent','DataStoreService','UpdateAsync','RemoteFunction','FireClient'):
            self.assertNotIn(term,luau)

if __name__=='__main__':
    unittest.main()
