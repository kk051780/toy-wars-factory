"""No-network negative and positive tests for the live RC source drift gate."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_live_intake import DOMAINS, PROJECT, evaluate, project_nodes


def fixture():
    required = sorted({"EGGRUMBLE_" + x for names in DOMAINS.values() for x in names})
    def make_project(names):
        server = {"$className": "ServerScriptService"}
        client = {"$className": "StarterPlayerScripts"}
        for name in names:
            if name in ("EGGRUMBLE_CombatFeel", "EGGRUMBLE_ProceduralSkills"):
                client[name] = {"$path": name + ".client.luau"}
            else:
                server[name] = {"$path": name + ".luau"}
        return {"tree": {"ServerScriptService": server,
                         "StarterPlayer": {"StarterPlayerScripts": client}}}
    author = make_project(required)
    quality = make_project(required)
    prefix = str(Path(PROJECT).parent).replace("\\", "/")
    blobs = {prefix + "/" + entry["path"].split("/")[-1]: "f" * 40
             for entry in project_nodes(author).values()}
    heads = {"author": "a" * 40, "quality": "b" * 40,
             "art": "c" * 40, "score": "d" * 40}
    prs = {name: {"head": {"sha": sha}, "base": {"sha": heads["author"]}}
           for name, sha in heads.items()}
    composer = "ref: " + heads["art"] + "\nref: " + heads["score"] + "\n"
    return prs, author, quality, composer, blobs, dict(blobs), "e" * 40


class SourceDriftGateTest(unittest.TestCase):
    def test_latest_all_domains_with_exact_composer_pins_is_review_only(self):
        args = fixture()
        result = evaluate(*args)
        self.assertEqual(result["decision"], "SOURCE_REVIEW_READY_ONLY")
        self.assertEqual(result["blockers"], [])
        self.assertEqual(len(result["domains"]), 8)
        self.assertEqual(result["official_rc_adopted"], "UNVERIFIED_REQUIRES_220_CAS_RECEIPT")

    def test_missing_new_boss_item_skill_modules_rejects_old_composite(self):
        prs, a, q, comp, ab, qb, rc = fixture()
        for n in ("EGGRUMBLE_BossSessionFence", "EGGRUMBLE_NeutralStoneGiant",
                  "EGGRUMBLE_RaidItemIntake", "EGGRUMBLE_ProceduralSkills"):
            for service in (q["tree"]["ServerScriptService"],
                            q["tree"]["StarterPlayer"]["StarterPlayerScripts"]):
                service.pop(n, None)
        prs["quality"]["base"]["sha"] = "1" * 40
        result = evaluate(prs, a, q, comp, ab, qb, rc)
        self.assertEqual(result["decision"], "SOURCE_RECONCILIATION_REQUIRED")
        self.assertFalse(result["domains"]["neutral"]["candidate_ready"])
        self.assertFalse(result["domains"]["item"]["candidate_ready"])
        self.assertIn("quality_base_not_latest_author_head", result["blockers"])

    def test_art_score_pin_stale_blocks_old_success(self):
        prs, a, q, comp, ab, qb, rc = fixture()
        comp = "ref: " + "0" * 40 + "\nref: " + "0" * 40
        result = evaluate(prs, a, q, comp, ab, qb, rc)
        self.assertIn("art_composer_pin_not_latest_head", result["blockers"])
        self.assertIn("score_composer_pin_not_latest_head", result["blockers"])

    def test_unowned_source_drift_fails_but_owned_override_is_flagged(self):
        prs, a, q, comp, ab, qb, rc = fixture()
        prefix = str(Path(PROJECT).parent).replace("\\", "/")
        qb[prefix + "/EGGRUMBLE_CombatBalance.luau"] = "1" * 40
        qb[prefix + "/EGGRUMBLE_BotActors.luau"] = "2" * 40
        result = evaluate(prs, a, q, comp, ab, qb, rc)
        self.assertEqual(result["unowned_identity_drifts"], ["EGGRUMBLE_CombatBalance"])
        self.assertEqual(result["quality_owned_overrides_needing_diff_review"], ["EGGRUMBLE_BotActors"])
        self.assertEqual(result["decision"], "SOURCE_RECONCILIATION_REQUIRED")

    def test_duplicate_script_name_is_rejected(self):
        _, a, _, _, _, _, _ = fixture()
        a["tree"]["StarterPlayer"]["StarterPlayerScripts"]["EGGRUMBLE_CombatBalance"] = {
            "$path": "EGGRUMBLE_CombatBalance.client.luau"}
        with self.assertRaisesRegex(ValueError, "duplicate executable name"):
            project_nodes(a)

    def test_partial_tree_can_never_be_trusted(self):
        from check_live_intake import tree_blobs
        with self.assertRaisesRegex(ValueError, "truncated"):
            tree_blobs({"truncated": True, "tree": []})


if __name__ == "__main__":
    unittest.main()
