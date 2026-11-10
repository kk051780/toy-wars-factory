import unittest
import random
from pathlib import Path
from oracle import Client, Server

ROOT=Path(__file__).resolve().parents[1]
SERVER=(ROOT/'luau/GoroganWarningDeadlineServer.luau').read_text('utf-8')
CLIENT=(ROOT/'luau/GoroganWarningDeadlineClient.luau').read_text('utf-8')

def warning(i=1, core=30, **kw):
    x={'kind':'STOMP_WARNING','attackId':i,'roundId':'m1','eventId':'e1','windupEnds':core+2}
    x.update(kw);return x

def clock(core=30,sync=100,**kw):
    x={'coreNow':core,'syncedServerNow':sync,'roundLive':True}
    x.update(kw);return x

def packet():return Server().stamp(warning(),clock())[0]

class ServerCases(unittest.TestCase):
    def test_disabled(self):
        with self.assertRaises(ValueError):Server(enabled=False)
    def test_unapproved(self):
        with self.assertRaises(ValueError):Server(approved=False)
    def test_invalid_ids(self):
        with self.assertRaises(ValueError):Server(event='a b')
    def test_wrong_stage(self):
        with self.assertRaises(ValueError):Server(stage='S4')
    def test_bad_epoch(self):
        with self.assertRaises(ValueError):Server(epoch=1.5)
    def test_first_stamp(self):
        p,r=Server().stamp(warning(),clock());self.assertEqual(r,'STAMPED');self.assertEqual(p['warningEndsServerTime'],102)
    def test_right_duration(self):
        p,r=Server().stamp(warning(core=30,windupEnds=31.3),clock());self.assertAlmostEqual(p['warningEndsServerTime'],101.3)
    def test_reject_late(self):self.assertEqual(Server().stamp(warning(core=30,windupEnds=29),clock())[1],'WARNING_NOT_LIVE')
    def test_reject_zero(self):self.assertEqual(Server().stamp(warning(core=30,windupEnds=30),clock())[1],'WARNING_NOT_LIVE')
    def test_reject_overlong(self):self.assertEqual(Server().stamp(warning(core=30,windupEnds=34),clock())[1],'WARNING_NOT_LIVE')
    def test_stale_match(self):self.assertEqual(Server().stamp(warning(roundId='m2'),clock())[1],'AUTHORITY_OR_COMMAND_INVALID')
    def test_stale_event(self):self.assertEqual(Server().stamp(warning(eventId='e2'),clock())[1],'AUTHORITY_OR_COMMAND_INVALID')
    def test_wrong_command(self):self.assertEqual(Server().stamp(warning(kind='STOMP_RESOLVE'),clock())[1],'AUTHORITY_OR_COMMAND_INVALID')
    def test_live_required(self):self.assertEqual(Server().stamp(warning(),clock(roundLive=False))[1],'AUTHORITY_OR_COMMAND_INVALID')
    def test_core_nan(self):self.assertEqual(Server().stamp(warning(),clock(core=float('nan')))[1],'AUTHORITY_OR_COMMAND_INVALID')
    def test_synced_nan(self):self.assertEqual(Server().stamp(warning(),clock(sync=float('nan')))[1],'AUTHORITY_OR_COMMAND_INVALID')
    def test_bad_attack_id(self):self.assertEqual(Server().stamp(warning(i=4),clock())[1],'AUTHORITY_OR_COMMAND_INVALID')
    def test_replay_attack(self):
        s=Server();s.stamp(warning(),clock());self.assertEqual(s.stamp(warning(),clock(core=31,sync=101))[1],'AUTHORITY_OR_COMMAND_INVALID')
    def test_two_attacks(self):
        s=Server();s.stamp(warning(),clock());p,r=s.stamp(warning(i=2,core=35),clock(core=35,sync=105));self.assertEqual(r,'STAMPED');self.assertEqual(p['attackId'],2)
    def test_clock_reversed_fail_closed(self):
        s=Server();s.stamp(warning(),clock());self.assertEqual(s.stamp(warning(i=2,core=29),clock(core=29,sync=105))[1],'CLOCK_REVERSED');self.assertTrue(s.closed)
    def test_synced_clock_reversed_fail_closed(self):
        s=Server();s.stamp(warning(),clock());self.assertEqual(s.stamp(warning(i=2,core=35),clock(core=35,sync=99))[1],'CLOCK_REVERSED')
    def test_does_not_mutate_source(self):
        w=warning();s=Server();p,_=s.stamp(w,clock());w['windupEnds']=0;self.assertEqual(p['warningEndsServerTime'],102)
    def test_close(self):
        s=Server();s.close();self.assertEqual(s.stamp(warning(),clock())[1],'CLOSED')

class ClientCases(unittest.TestCase):
    def test_wrong_stage(self):
        with self.assertRaises(ValueError):Client(stage='S2')
    def test_default_accept(self):
        p,r=Client().accept(packet(),100.1);self.assertEqual(r,'RENDER_REMAINING');self.assertAlmostEqual(p['remainingSeconds'],1.9)
    def test_late_arrival_093(self):
        p,r=Client().accept(packet(),101.07);self.assertEqual(r,'RENDER_REMAINING');self.assertAlmostEqual(p['remainingSeconds'],.93)
    def test_network_expired(self):self.assertEqual(Client().accept(packet(),102.01)[1],'LATE_EXPIRED')
    def test_no_new_two_seconds_after_delay(self):self.assertLess(Client().accept(packet(),101.5)[0]['remainingSeconds'],.6)
    def test_bad_kind(self):self.assertEqual(Client().accept({**packet(),'kind':'START'},100.1)[1],'INVALID_IDENTITY_OR_REPLAY')
    def test_wrong_boss(self):self.assertEqual(Client().accept({**packet(),'bossId':'LIGARDO'},100.1)[1],'INVALID_IDENTITY_OR_REPLAY')
    def test_wrong_match(self):self.assertEqual(Client().accept({**packet(),'matchId':'m2'},100.1)[1],'INVALID_IDENTITY_OR_REPLAY')
    def test_wrong_epoch(self):self.assertEqual(Client().accept({**packet(),'epoch':2},100.1)[1],'INVALID_IDENTITY_OR_REPLAY')
    def test_visual_stopped(self):
        c=Client();self.assertEqual(c.accept(packet(),100.1,False)[1],'VISUAL_ENDED');self.assertTrue(c.closed)
    def test_packet_replay(self):
        c=Client();c.accept(packet(),100.1);self.assertEqual(c.accept(packet(),100.2)[1],'INVALID_IDENTITY_OR_REPLAY')
    def test_attack_increases(self):
        c=Client();p=packet();c.accept(p,100.1);p['attackId']=2;p['sentServerTime']=105;p['warningEndsServerTime']=107
        self.assertEqual(c.accept(p,105.1)[1],'RENDER_REMAINING')
    def test_reject_future_stamp(self):self.assertEqual(Client().accept(packet(),99)[1],'BAD_SERVER_DEADLINE')
    def test_reject_overlong(self):self.assertEqual(Client().accept({**packet(),'warningEndsServerTime':110},100.1)[1],'BAD_SERVER_DEADLINE')
    def test_invalid_clock_closes(self):
        c=Client();self.assertEqual(c.accept(packet(),float('nan'))[1],'CLOCK_INVALID');self.assertTrue(c.closed)
    def test_clock_backward_closes(self):
        c=Client();c.accept(packet(),100.2);self.assertEqual(c.accept({**packet(),'attackId':2},100.1)[1],'CLOCK_INVALID')
    def test_remaining(self):
        c=Client();c.accept(packet(),100.1);self.assertAlmostEqual(c.remaining(101),1);self.assertEqual(c.remaining(102.1),0)
    def test_remaining_inactive(self):
        c=Client();c.accept(packet(),100.1);self.assertEqual(c.remaining(101,False),0)
    def test_remaining_time_reverse(self):
        c=Client();c.accept(packet(),101);self.assertEqual(c.remaining(100.9),0)
    def test_close(self):
        c=Client();c.accept(packet(),100.1);c.close();self.assertEqual(c.remaining(100.2),0)
    def test_client_rejects_attack_nan(self):self.assertEqual(Client().accept({**packet(),'attackId':float('nan')},100.1)[1],'INVALID_IDENTITY_OR_REPLAY')

class SourceStaticCases(unittest.TestCase):
    def test_no_subscribers(self):
        for src in (SERVER,CLIENT):
            for bad in ('OnClientEvent:Connect','OnServerEvent:Connect','Heartbeat:Connect','FireAllClients(', 'TakeDamage(', 'DataStoreService', 'PathfindingService'):
                self.assertNotIn(bad,src)
    def test_no_local_restarted_two_seconds(self):
        live='\n'.join(line for line in CLIENT.splitlines() if not line.lstrip().startswith('--'))
        self.assertNotIn('os.clock',live);self.assertNotIn('now+2',live)
    def test_required_clock_stamp(self):
        for name in ('syncedServerNow','windupEnds','STOMP_WARNING','warningEndsServerTime'):
            self.assertIn(name,SERVER)
    def test_requires_existing_visual_lifecycle(self):
        self.assertIn('active~=true',CLIENT);self.assertIn('VISUAL_ENDED',CLIENT)
    def test_single_event_without_visual_damage(self):
        for src in (SERVER,CLIENT):
            self.assertNotIn('require(',src);self.assertNotIn('Instance.new',src)
    def test_jitter_random(self):
        rand=random.Random(42)
        for _ in range(1000):
            offset=rand.uniform(0,3)
            p,r=Client().accept(packet(),100+offset)
            if offset<2:
                self.assertEqual(r,'RENDER_REMAINING');self.assertAlmostEqual(p['remainingSeconds'],2-offset)
            else:self.assertEqual(r,'LATE_EXPIRED')

if __name__=='__main__':unittest.main()
