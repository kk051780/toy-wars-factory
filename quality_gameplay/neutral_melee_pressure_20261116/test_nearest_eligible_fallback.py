"""Model + source-structure regression for GQ nearest eligible neutral melee.

The model does NOT claim Roblox engine execution. Native Luau and private Rojo
source checks remain separate steps in the existing #533 workflow.
"""
from __future__ import annotations

import unittest
from compose_melee_candidate import GAME, patch


def select_victim(targets, *, now=10.0, soldier_last=None, victim_last=None,
                  soldier_alive=True, active=True, ray_budget=24):
    """Independent deterministic oracle for the intended ONE-hit Swarm tick."""
    victim_last = dict(victim_last or {})
    if not active or not soldier_alive:
        return None, 0, soldier_last, victim_last
    if soldier_last is not None and now - soldier_last < 1.4:
        return None, 0, soldier_last, victim_last

    eligible = []
    for i, target in enumerate(targets):
        distance = target["distance"]
        prior = victim_last.get(target["id"])
        if (target.get("alive", True) and 0 <= distance <= 4.25
                and (prior is None or now - prior >= 0.8)):
            eligible.append((distance, i, target))
    eligible.sort(key=lambda row: (row[0], row[1]))

    used = 0
    for _, _, target in eligible:
        if used >= ray_budget:
            break
        used += 1
        if not target.get("visible", True):
            continue
        victim_last[target["id"]] = now
        return target["id"], used, now, victim_last
    return None, used, soldier_last, victim_last


class NeutralMeleeFallback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original = (GAME / "EGGRUMBLE_SwarmCombat.luau").read_text(encoding="utf-8")
        cls.composed = patch(original)

    def test_source_selects_ready_before_sort_and_spends_ray_only_after_budget(self):
        src = self.composed.split("-- Select the nearest READY candidate", 1)[1]
        self.assertEqual(src.count("candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"), 1)
        self.assertNotIn("nearest.humanoid:TakeDamage(Melee.DAMAGE)", src)
        self.assertLess(src.index("Melee.ready("), src.index("table.sort(eligible"))
        self.assertLess(src.index("table.sort(eligible"), src.index("for _,candidate in ipairs(eligible)"))
        self.assertLess(src.index("if meleeRays>=Melee.MAX_RAYS_PER_TICK then break end"),
                        src.index("meleeRays+=1"))
        self.assertLess(src.index("meleeRays+=1"),
                        src.index("if meleeLineClear(m,candidate.victim.root) then"))
        self.assertLess(src.index("if meleeLineClear(m,candidate.victim.root) then"),
                        src.index("Melee.commit(lastMeleeSwing"))
        self.assertLess(src.index("Melee.commit(lastMeleeSwing"),
                        src.index("candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"))
        self.assertIn("break -- One real hit per soldier swing.", src)
        self.assertIn("if a.distance==b.distance then return a.slot<b.slot end", src)

    def test_nearest_on_cooldown_falls_back(self):
        t = [{"id":"near","distance":1}, {"id":"far","distance":2}]
        hit, rays, _, stamps = select_victim(t, victim_last={"near":9.4})
        self.assertEqual((hit, rays), ("far", 1))
        self.assertEqual(stamps["near"], 9.4)

    def test_nearest_behind_wall_falls_back(self):
        t = [{"id":"wall","distance":1,"visible":False},
             {"id":"open","distance":2,"visible":True}]
        hit, rays, _, stamps = select_victim(t)
        self.assertEqual((hit, rays), ("open", 2))
        self.assertNotIn("wall", stamps)

    def test_two_walls_consume_only_two_rays_and_no_cooldown(self):
        t = [{"id":"a","distance":1,"visible":False},
             {"id":"b","distance":2,"visible":False}]
        self.assertEqual(select_victim(t)[:3], (None, 2, None))

    def test_wall_fallback_does_not_bypass_global_ray_budget(self):
        t = [{"id":"wall","distance":1,"visible":False},
             {"id":"open","distance":2}]
        self.assertEqual(select_victim(t, ray_budget=1)[:3], (None, 1, None))
        self.assertEqual(select_victim(t, ray_budget=0)[:3], (None, 0, None))

    def test_exact_cooldown_boundaries(self):
        t = [{"id":"a","distance":1}]
        self.assertEqual(select_victim(t, soldier_last=8.6, victim_last={"a":9.2})[0], "a")
        self.assertIsNone(select_victim(t, soldier_last=8.6001)[0])
        self.assertIsNone(select_victim(t, victim_last={"a":9.2001})[0])

    def test_dead_inactive_and_out_of_range_rejected(self):
        t = [{"id":"dead","distance":1,"alive":False},
             {"id":"far","distance":4.26},
             {"id":"negative","distance":-0.1}]
        self.assertEqual(select_victim(t)[0], None)
        self.assertEqual(select_victim([{"id":"a","distance":1}],active=False)[0], None)
        self.assertEqual(select_victim([{"id":"a","distance":1}],soldier_alive=False)[0], None)

    def test_equal_distance_order_is_stable(self):
        t = [{"id":"first","distance":2}, {"id":"second","distance":2}]
        self.assertEqual(select_victim(t)[0], "first")

    def test_one_hit_commits_soldier_and_target_cd(self):
        t = [{"id":"first","distance":1}, {"id":"second","distance":2}]
        hit, rays, soldier_stamp, stamps = select_victim(t)
        self.assertEqual((hit,rays,soldier_stamp),("first",1,10.0))
        self.assertEqual(stamps, {"first":10.0})
        self.assertIsNone(select_victim(t, soldier_last=soldier_stamp, victim_last=stamps)[0])

    def test_crowd_does_not_exceed_los_budget(self):
        t = [{"id":str(i),"distance":1.0+i/100,"visible":False} for i in range(40)]
        self.assertEqual(select_victim(t,ray_budget=24)[:3], (None,24,None))


if __name__ == "__main__":
    unittest.main()
