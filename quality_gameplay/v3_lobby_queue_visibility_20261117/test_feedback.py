#!/usr/bin/env python3
"""Fail-closed source-selection contract; no game / RC / main mutation."""
import sys
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
from select_feedback import apply, CHANGES

ORIGINAL=Path("_original482/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_LobbyCastleModesPreview.server.luau")

class LobbyQueueFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=ORIGINAL.read_text(encoding="utf-8")

    def test_real_original_select(self):
        v=apply(self.source)
        self.assertIn('local queueStartedAt:{[string]:number}={}',v)
        self.assertIn('refreshQueueBoard(mode)',v)
        self.assertGreater(len(v),len(self.source))
        self.assertEqual(v.count('local function refreshQueueBoard(mode:string)'),1)

    def test_off_byte_exact(self):
        after=apply(self.source)
        original=after
        for old,new in reversed(CHANGES):
            if new!=old:
                self.assertEqual(original.count(new),1)
                original=original.replace(new,old,1)
        self.assertEqual(original,self.source)

    def test_no_second_game_remote_gui_session(self):
        v=apply(self.source)
        for anchor in ('Instance.new("BillboardGui")','Instance.new("RemoteEvent")','local sessions:{[string]:any}={}',
                       'local joined:{[number]:string}={}','local function startSession(mode:string)',
                       'Rules.start(session.rules)','BotActors.start(session,Rules)','SwarmCombat.start(session)'):
            self.assertEqual(v.count(anchor),self.source.count(anchor),anchor)

    def test_one_authoritative_countdown_only(self):
        v=apply(self.source)
        self.assertEqual(v.count('task.delay(COUNTDOWN,'),1)
        self.assertEqual(v.count('startSession(mode)'),2)
        self.assertIn('queueEpoch[mode]~=expectedEpoch or sessions[mode]',v)
        self.assertIn('task.wait(1)',v)

    def test_mode_isolation(self):
        v=apply(self.source)
        self.assertIn('for mode,gate in pairs({TEAM=gateTeam,BATTLE_ROYALE=gateBR})',v)
        self.assertIn('local label=queueBoards[mode]',v)
        self.assertIn('local started=queueStartedAt[mode] or time()',v)
        self.assertIn('local waiting=queues[mode]',v)

    def test_cancel_resets_old_queue_start(self):
        v=apply(self.source)
        self.assertIn('if #queues[previous]==0 then queueStartedAt[previous]=nil end',v)
        self.assertIn('if previous==mode then return end',v)
        self.assertIn('queueEpoch[mode]+=1\n  refreshQueueBoard(mode)',v)

    def test_disconnect_resets_empty_queue(self):
        v=apply(self.source)
        self.assertIn('if #queues[mode]==0 then queueStartedAt[mode]=nil end',v)
        self.assertIn('RoundReplay.leaveWaitingQueue(mode,p,queues,joined,queueEpoch,sessions)',v)

    def test_started_mode_sets_status(self):
        v=apply(self.source)
        self.assertIn('if sessions[mode] then\n  label.Text=prefix..',v)
        self.assertIn('session.world.Name=mode.."_Arena";session.world.Parent=folder\n  refreshQueueBoard(mode)',v)

    def test_no_empty_queue_countdown(self):
        v=apply(self.source)
        self.assertIn('if count==0 then',v)
        self.assertIn('if queueEpoch[mode]~=expectedEpoch or sessions[mode] or #queues[mode]==0 then return end',v)

    def test_board_visibility_owner_unmodified(self):
        v=apply(self.source)
        self.assertEqual(v.count('b.AlwaysOnTop=true'),self.source.count('b.AlwaysOnTop=true'))
        self.assertIn('local bb=gate:FindFirstChildOfClass("BillboardGui")',v)
        self.assertIn('txt and txt:IsA("TextLabel")',v)

    def test_reapply_rejected(self):
        with self.assertRaisesRegex(ValueError,"already installed"):
            apply(apply(self.source))

    def test_missing_queue_epoch_rejected(self):
        with self.assertRaisesRegex(ValueError,"contract missing"):
            apply(self.source.replace('local queueEpoch:', 'local oldQueueEpoch:',1))

    def test_changed_countdown_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError,"multiplicity"):
            apply(self.source.replace("local COUNTDOWN=12 -- seconds for private preview only",
                                      "local COUNTDOWN=13 -- seconds for private preview only",1))

    def test_duplicate_portal_prompt_rejected(self):
        with self.assertRaisesRegex(ValueError,"multiplicity"):
            apply(self.source.replace('prompt(gateTeam,"参加する"',
                                      'prompt(gateTeam,"参加する"\n'+'prompt(gateTeam,"参加する"',1))

    def test_missing_author_join_rejected(self):
        with self.assertRaisesRegex(ValueError,"multiplicity"):
            apply(self.source.replace(' if #queues[mode]==1 then\n  local expectedEpoch=queueEpoch[mode]\n',
                                      ' if #queues[mode]==1 then\n  local oldEpoch=queueEpoch[mode]\n',1))

if __name__=="__main__":
    unittest.main()
