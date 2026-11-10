import random
import unittest
from catalog_reference import Catalog, ITEMS, SLOTS, MAX_SESSION_PLAYERS

class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.active={1,2,3}
        self.grants={(1,'egg_glow_amber'),(2,'lobby_plinth_jade')}
        self.c=Catalog(lambda p:p in self.active,lambda p,i:(p,i) in self.grants)
    def test_all_items(self):self.assertEqual(len(ITEMS),5)
    def test_unique_slots(self):self.assertEqual(len({x[0] for x in ITEMS.values()}),5)
    def test_prices_absent(self):self.assertFalse(any('price' in x for x in ITEMS))
    def test_list_order(self):self.assertEqual([x['itemId'] for x in self.c.list(1)[0]],list(ITEMS))
    def test_view_no_pii(self):self.assertNotIn('player',str(self.c.list(1)))
    def test_view_noncombat(self):self.assertTrue(all(x['noCombatStats'] for x in self.c.list(1)[0]))
    def test_preview_all(self):
        for i in ITEMS:self.assertEqual(self.c.preview(1,i)[1],'OK')
    def test_preview_does_not_equip(self):self.c.preview(1,'victory_petals');self.assertEqual(self.c.selected,{})
    def test_preview_starter_owned(self):self.assertTrue(self.c.preview(2,'banner_starter')[0]['owned'])
    def test_preview_entitled_owned(self):self.assertTrue(self.c.preview(1,'egg_glow_amber')[0]['owned'])
    def test_preview_unowned(self):self.assertFalse(self.c.preview(3,'egg_glow_amber')[0]['owned'])
    def test_preview_future_not_owned(self):self.assertFalse(self.c.preview(2,'victory_petals')[0]['owned'])
    def test_list_inactive(self):self.assertEqual(self.c.list(9)[1],'NOT_ACTIVE')
    def test_preview_inactive(self):self.assertEqual(self.c.preview(9,'banner_starter')[1],'NOT_ACTIVE')
    def test_equip_starter(self):self.assertEqual(self.c.equip(1,'banner_starter')[1],'EQUIPPED')
    def test_equip_idempotent(self):self.c.equip(1,'banner_starter');self.assertEqual(self.c.equip(1,'banner_starter')[1],'ALREADY_EQUIPPED')
    def test_equip_preview_denied(self):self.assertEqual(self.c.equip(1,'victory_petals')[1],'NOT_OWNED')
    def test_equip_future_even_if_granted(self):
        self.grants.add((1,'victory_petals'));self.assertEqual(self.c.equip(1,'victory_petals')[1],'NOT_OWNED')
    def test_equip_unowned(self):self.assertEqual(self.c.equip(3,'lobby_plinth_jade')[1],'NOT_OWNED')
    def test_equip_owned(self):self.assertEqual(self.c.equip(1,'egg_glow_amber')[1],'EQUIPPED')
    def test_equip_multiple_slots(self):
        self.c.equip(1,'banner_starter');self.c.equip(1,'egg_glow_amber');self.assertEqual(len(self.c.equipped(1)[0]),2)
    def test_equip_not_active(self):self.assertEqual(self.c.equip(9,'banner_starter')[1],'NOT_ACTIVE')
    def test_equip_unknown(self):self.assertEqual(self.c.equip(1,'fake_item')[1],'INVALID_ITEM')
    def test_equip_bad_type(self):self.assertEqual(self.c.equip(1,{'id':'banner_starter'})[1],'INVALID_ITEM')
    def test_equip_long_id(self):self.assertEqual(self.c.equip(1,'a'*100)[1],'INVALID_ITEM')
    def test_equip_injection(self):self.assertEqual(self.c.equip(1,'banner_starter;purchase=1')[1],'INVALID_ITEM')
    def test_revoke_entitlement(self):
        self.c.equip(1,'egg_glow_amber');self.grants.clear();self.assertEqual(self.c.equipped(1)[0],{})
    def test_revoke_then_return(self):
        self.c.equip(1,'egg_glow_amber');self.grants.clear();self.assertEqual(self.c.equip(1,'egg_glow_amber')[1],'NOT_OWNED')
    def test_unequip(self):
        self.c.equip(1,'banner_starter');self.assertEqual(self.c.unequip(1,'BANNER')[1],'UNEQUIPPED')
    def test_unequip_empty(self):self.assertEqual(self.c.unequip(1,'BANNER')[1],'ALREADY_EMPTY')
    def test_unequip_unknown(self):self.assertEqual(self.c.unequip(1,'PAYMENT')[1],'INVALID_SLOT')
    def test_unequip_not_active(self):self.assertEqual(self.c.unequip(7,'BANNER')[1],'NOT_ACTIVE')
    def test_player_left(self):self.c.equip(1,'banner_starter');self.c.player_left(1);self.assertEqual(self.c.selected,{})
    def test_player_left_idempotent(self):self.c.player_left(1);self.c.player_left(1);self.assertEqual(self.c.selected,{})
    def test_reset_session(self):self.c.equip(1,'banner_starter');self.c.reset_session();self.assertEqual(self.c.selected,{})
    def test_view_saved_false(self):self.assertTrue(all(x['saved'] is False for x in self.c.list(1)[0]))
    def test_view_purchase_disabled(self):self.assertTrue(all(x['purchaseEnabled'] is False for x in self.c.list(1)[0]))
    def test_particle_budget(self):self.assertLessEqual(max(x[2] for x in ITEMS.values()),12)
    def test_default_no_selection(self):self.assertEqual(self.c.equipped(1),({},'OK'))
    def test_invalid_user_ids(self):
        for p in [-1,0,1.5,None,'','*',{},'X'*65,True]:
            self.assertEqual(self.c.list(p)[1],'NOT_ACTIVE')
    def test_alphanumeric_server_session_key(self):
        self.active.add('abc-123');self.assertEqual(self.c.equip('abc-123','banner_starter')[1],'EQUIPPED')
    def test_truthy_not_true_active(self):
        c=Catalog(lambda p:1,lambda p,i:True);self.assertEqual(c.list(1)[1],'NOT_ACTIVE')
    def test_truthy_not_true_entitlement(self):
        c=Catalog(lambda p:True,lambda p,i:1);self.assertEqual(c.equip(1,'egg_glow_amber')[1],'NOT_OWNED')
    def test_active_callback_failure(self):
        def f(p):raise RuntimeError('offline')
        c=Catalog(f,lambda p,i:True);self.assertEqual(c.equip(1,'banner_starter')[1],'NOT_ACTIVE')
    def test_entitlement_callback_failure(self):
        def f(p,i):raise RuntimeError('offline')
        c=Catalog(lambda p:True,f);self.assertEqual(c.equip(1,'egg_glow_amber')[1],'NOT_OWNED')
    def test_starter_resolver_failure_still_free(self):
        def f(p,i):raise RuntimeError('offline')
        c=Catalog(lambda p:True,f);self.assertEqual(c.equip(1,'banner_starter')[1],'EQUIPPED')
    def test_capacity(self):
        c=Catalog(lambda p:True,lambda p,i:True)
        for p in range(1,MAX_SESSION_PLAYERS+1):self.assertEqual(c.equip(p,'banner_starter')[1],'EQUIPPED')
        self.assertEqual(c.equip(999,'banner_starter')[1],'SESSION_CAPACITY')
    def test_capacity_freed_on_leave(self):
        c=Catalog(lambda p:True,lambda p,i:True)
        for p in range(1,MAX_SESSION_PLAYERS+1):c.equip(p,'banner_starter')
        c.player_left(1);self.assertEqual(c.equip(999,'banner_starter')[1],'EQUIPPED')
    def test_no_player_ids_in_view(self):self.assertNotIn('1',str(self.c.list(1)[0][0].keys()))
    def test_random_sequences_invariant(self):
        rng=random.Random(5012)
        for _ in range(2000):
            p=rng.choice([1,2,3]);item=rng.choice(list(ITEMS))
            op=rng.choice(('equip','preview','unequip','leave','revoke'))
            if op=='equip':self.c.equip(p,item)
            elif op=='preview':self.c.preview(p,item)
            elif op=='unequip':self.c.unequip(p,ITEMS[item][0])
            elif op=='leave':self.c.player_left(p)
            else:self.grants.discard((p,item))
            self.assertLessEqual(len(self.c.selected),3)
            for who in (1,2,3):
                visible,status=self.c.equipped(who)
                self.assertEqual(status,'OK')
                self.assertTrue(all(info['owned'] for info in visible.values()))
                self.assertTrue(all(info['noCombatStats'] for info in visible.values()))
    def test_preview_no_mutation_1000(self):
        for _ in range(1000):self.c.preview(1,'dragon_wave_emote')
        self.assertEqual(self.c.selected,{})
    def test_many_rejected_equip_no_capacity(self):
        for _ in range(1000):self.c.equip(1,'victory_petals')
        self.assertEqual(len(self.c.selected),0)
    def test_output_does_not_expose_own_function(self):self.assertNotIn('owns',str(self.c.list(1)[0]))

if __name__=='__main__':unittest.main()
