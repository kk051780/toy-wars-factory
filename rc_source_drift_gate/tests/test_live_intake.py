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
                  "EGGRUMBLE_RaidItemIntake", "EGGRUMBLE_ProceduralSkills",
                  "EGGRUMBLE_DivineMantle"):
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


# The active 26-script composer differs deliberately from the old 16-script
# game-core Rojo map. Test the actual 26-Place intake independently of legacy.
from check_live_intake import (evaluate_active26, CURRENT26_COMPOSER, CURRENT26_WORKFLOW,
                               CURRENT26_RUN_NAME, current26_pins)


def current26_fixture():
    prs, author, _old_quality, oldworkflow, blobs, _, rc = fixture()
    # One additional old-author source not explicitly in the compact domain core.
    author["tree"]["ServerScriptService"]["EGGRUMBLE_SkillFX"] = {
        "$path": "EGGRUMBLE_SkillFX.luau"}
    prefix = str(Path(PROJECT).parent).replace("\\", "/")
    blobs[prefix + "/EGGRUMBLE_SkillFX.luau"] = "f" * 40
    quality_blobs = {CURRENT26_COMPOSER: "0" * 40, CURRENT26_WORKFLOW: "1" * 40}
    workflow = ("Read fixed latest game SOURCE from original author PR482\n"
                + "  ref: " + prs["author"]["head"]["sha"] + "\n"
                + "Read fixed original ART source from PR485\n"
                + "  ref: " + prs["art"]["head"]["sha"] + "\n"
                + "Read fixed original SCORE source from PR487\n"
                + "  ref: " + prs["score"]["head"]["sha"] + "\n"
                + "Build fixed Luau native compiler and test runner\n")
    composer = "\n".join((
        "def apply_ramp(", "EGGRUMBLE_BotActors", "EGGRUMBLE_BotPathRouter",
        "EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_ProceduralSkills",
        "EGGRUMBLE_RaidItemIntake", "EGGRUMBLE_NeutralStoneGiant",
        "EGGRUMBLE_BossSessionFence", "EGGRUMBLE_ScoreBalance",
        "EGGRUMBLE_ArtDistanceLOD", "assert len(server)-1==23 and len(client)-1==3",
        "assert len(mapped)==26", '"source_sha256"'
    ))
    ci = [{"name": CURRENT26_RUN_NAME, "head_sha": prs["quality"]["head"]["sha"],
           "id": 987654321, "status": "completed", "conclusion": "success",
           "html_url": "https://github.com/example/workflows/987654321"}]
    return [prs, author, blobs, quality_blobs, workflow, composer, ci, rc]


class Current26IntakeTest(unittest.TestCase):
    def test_current26_pass_never_claims_rc_or_studio(self):
        result = evaluate_active26(*current26_fixture())
        self.assertEqual(result["decision"], "SOURCE_REVIEW_READY_ONLY")
        self.assertEqual(result["target_candidate_script_count"], 26)
        self.assertEqual(result["composite_ci"]["run_id"], 987654321)
        self.assertEqual(result["official_rc_adopted"], "NOT_VERIFIED_REQUIRES_220_CAS_RECEIPT")
        self.assertEqual(result["studio_android_art_fun_owner"], "NOT_VERIFIED")

    def test_current26_ignores_old21_composite_without_giving_forged_pass(self):
        args = current26_fixture()
        self.assertEqual(len(current26_pins(args[4])), 3)
        self.assertTrue(evaluate_active26(*args)["obsolete_21_source_workflow_not_used_as_latest_proof"])

    def test_current26_missing_new_boss_blocks(self):
        args = current26_fixture()
        del args[1]["tree"]["ServerScriptService"]["EGGRUMBLE_BossSessionFence"]
        result = evaluate_active26(*args)
        self.assertEqual(result["decision"], "SOURCE_RECONCILIATION_REQUIRED")
        self.assertTrue(any("author_contract_missing:neutral" in x for x in result["blockers"]))

    def test_current26_detects_stale_score_pin(self):
        args = current26_fixture()
        args[4] = args[4].replace("  ref: " + "d"*40, "  ref: " + "e"*40)
        self.assertIn("current26_score_pin_stale", evaluate_active26(*args)["blockers"])

    def test_current26_success_on_old_head_is_not_same_head_success(self):
        args = current26_fixture()
        args[6][0]["head_sha"] = "9" * 40
        self.assertIn("current26_samehead_CI_not_success", evaluate_active26(*args)["blockers"])

    def test_current26_pending_ci_is_not_pass(self):
        args = current26_fixture()
        args[6][0]["conclusion"] = None
        args[6][0]["status"] = "in_progress"
        self.assertIn("current26_samehead_CI_not_success", evaluate_active26(*args)["blockers"])

    def test_current26_missing_composer_contract_is_red(self):
        args = current26_fixture()
        args[5] = args[5].replace("EGGRUMBLE_RaidItemIntake", "UNRELATED")
        self.assertTrue(any("current26_composer_contract_missing" in x
                            for x in evaluate_active26(*args)["blockers"]))

    def test_current26_mapped_source_blob_absence_is_red(self):
        args = current26_fixture()
        args[2].clear()
        self.assertTrue(any("author_blob_unknown" in x
                            for x in evaluate_active26(*args)["blockers"]))
