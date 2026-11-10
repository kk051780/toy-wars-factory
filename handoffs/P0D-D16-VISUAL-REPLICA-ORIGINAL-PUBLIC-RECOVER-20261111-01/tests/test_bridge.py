import unittest
from reference.bridge import build
from reference.client_policy import Policy

GOOD=dict(matchId='round-A',eventId='event-1',status='ACTIVE',kind='GIANT_ONE',targets=['101'],scaleMilli=1600,expiresAt=21)
class BridgeTests(unittest.TestCase):
    def test_bridge_client_round_trip(self):
        payload,err=build(GOOD,13)
        self.assertIsNone(err)
        self.assertEqual(payload['remainingSeconds'],8)
        client=Policy('round-A')
        self.assertTrue(client.accept(payload,'round-A',140)[0]);self.assertEqual(client.tick('round-A',148),'EXPIRED')
    def test_client_clock_never_used_for_server_ttl(self):
        payload,_=build(GOOD,15);self.assertEqual(payload['remainingSeconds'],6)
        self.assertEqual(payload['matchId'],GOOD['matchId'])
    def test_giant_ttl_boundary(self):
        self.assertEqual(build(GOOD,21)[1],'INVALID_ACTIVE_TTL')
        self.assertEqual(build(GOOD,12.9)[1],'INVALID_ACTIVE_TTL')
    def test_invalid_expiry(self):
        for t in (float('inf'),float('nan'),-4,False,'21',None):
            with self.subTest(t=t):self.assertIsNotNone(build(dict(GOOD,expiresAt=t),13)[1])
    def test_invalid_elapsed(self):
        for t in (float('inf'),float('nan'),-1,False,'13',None):
            with self.subTest(t=t):self.assertIsNotNone(build(GOOD,t)[1])
    def test_bad_roster(self):
        for roster in ([],['101','101'],['123','101'],[5],list(map(str,range(17)))):
            with self.subTest(roster=roster):self.assertEqual(build(dict(GOOD,targets=roster),13)[1],'INVALID_TARGETS')
    def test_terminal_clears(self):
        for s in ('EXPIRED','CLOSED'):
            with self.subTest(status=s):
                data,err=build(dict(GOOD,status=s,targets=[]),80)
                self.assertIsNone(err);self.assertEqual(data['targets'],[]);self.assertEqual(data['remainingSeconds'],0)
    def test_terminal_with_targets_rejected(self):
        self.assertEqual(build(dict(GOOD,status='EXPIRED'),22)[1],'INVALID_TERMINAL')
    def test_different_event_unknown(self):
        self.assertEqual(build(dict(GOOD,status='IDLE'),13)[1],'UNEXPECTED_STATUS')
    def test_bridge_no_authority_data(self):
        data,_=build(dict(GOOD,damage=5000,owner='client',cash=10000),13)
        self.assertNotIn('damage',data);self.assertNotIn('owner',data);self.assertNotIn('cash',data)

if __name__=='__main__': unittest.main()
