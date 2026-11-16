"""Positive + negative source-lineage tests; never require Roblox Studio."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from validate import CLIENT, MANDATORY, SCHEMA, SERVER, check

AUTHOR = "a" * 40
RC = "b" * 40
CANDIDATE = "c" * 40


class TestRCLineage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.author = root / "author"
        self.candidate = root / "candidate"
        self.author.mkdir()
        self.candidate.mkdir()
        self.project = {
            "name": "EGGRUMBLE_V3_TEST_SOURCE_ONLY",
            "tree": {"$className": "DataModel", "ServerScriptService": {
                "$className": "ServerScriptService"
            }, "StarterPlayer": {"$className": "StarterPlayer",
                "StarterPlayerScripts": {"$className": "StarterPlayerScripts"}}},
        }
        for name in sorted(MANDATORY):
            if name in ("EGGRUMBLE_CombatFeel", "EGGRUMBLE_ProceduralSkills"):
                path = name + ".client.luau"
                dst = self.project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
            elif name == "EGGRUMBLE_LobbyCastleModesPreview":
                path = name + ".server.luau"
                dst = self.project["tree"]["ServerScriptService"]
            else:
                path = name + ".luau"
                dst = self.project["tree"]["ServerScriptService"]
            dst[name] = {"$path": path}
            for folder in (self.author, self.candidate):
                (folder / path).write_text("-- strict placeholder\nreturn {}\n", encoding="utf-8")
        self.author_project = self.author / "project.json"
        self.candidate_project = self.candidate / "project.json"
        self.sync_projects()
        self.provenance = {
            "schema": SCHEMA,
            "author_sha": AUTHOR,
            "candidate_sha": CANDIDATE,
            "rc_sha": RC,
            "overlays": {},
        }

    def sync_projects(self):
        for path in (self.author_project, self.candidate_project):
            path.write_text(json.dumps(self.project), encoding="utf-8")

    def run_check(self):
        return check(
            self.author, self.candidate,
            self.author_project, self.candidate_project,
            self.provenance, AUTHOR, RC
        )

    def test_unchanged_all_21_sources_pass(self):
        outcome = self.run_check()
        self.assertEqual(outcome["status"], "SOURCE_GATE_PASS", outcome["errors"])
        self.assertEqual(outcome["source_count_candidate"], 21)
        self.assertEqual(len(outcome["domain_inventory"]), 8)
        self.assertEqual(outcome["changed_sources"], [])
        self.assertFalse(outcome["official_rc_integrated"])

    def test_stale_author_branch_blocked(self):
        self.provenance["author_sha"] = "e" * 40
        self.assertIn("STALE_AUTHOR", " ".join(self.run_check()["errors"]))

    def test_stale_official_rc_branch_blocked(self):
        self.provenance["rc_sha"] = "d" * 40
        self.assertIn("STALE_RC", " ".join(self.run_check()["errors"]))

    def test_author_module_changed_without_claim_blocked(self):
        f = self.candidate / "EGGRUMBLE_CastleMatchRules.luau"
        f.write_text("return { changed=true }\n", encoding="utf-8")
        self.assertIn("lacks owner-scoped overlay", " ".join(self.run_check()["errors"]))

    def test_author_module_with_explicit_claim_passes(self):
        name = "EGGRUMBLE_BotActors"
        f = self.candidate / (name + ".luau")
        before = hashlib.sha256(f.read_bytes()).hexdigest()
        f.write_text("return { changed=true }\n", encoding="utf-8")
        after = hashlib.sha256(f.read_bytes()).hexdigest()
        self.provenance["overlays"] = {
            name: {"owner": "#484", "feature_id": "FB-AI-NAV",
                   "reason": "Reviewed isolated source fix", "rollback": before,
                   "sha256": after, "original_sha256": before}
        }
        out = self.run_check()
        self.assertEqual(out["status"], "SOURCE_GATE_PASS", out["errors"])
        self.assertEqual(out["changed_sources"], [name])

    def test_modified_digest_or_unpinned_predecessor_rejected(self):
        self.test_author_module_with_explicit_claim_passes()
        overlay = self.provenance["overlays"]["EGGRUMBLE_BotActors"]
        overlay["sha256"] = "0" * 64
        overlay["original_sha256"] = "1" * 64
        self.assertIn("source hash differs", " ".join(self.run_check()["errors"]))
        self.assertIn("predecessor was not pinned", " ".join(self.run_check()["errors"]))

    def test_missing_new_stone_giant_dependency_rejected(self):
        self.project["tree"]["ServerScriptService"].pop("EGGRUMBLE_BossSessionFence")
        self.candidate_project.write_text(json.dumps(self.project), encoding="utf-8")
        out = self.run_check()
        self.assertIn("mandatory V3 source missing", " ".join(out["errors"]))
        self.assertIn("deleted author source", " ".join(out["errors"]))

    def test_extra_unknown_server_script_cannot_be_silent(self):
        p = self.candidate / "RogueGame.server.luau"
        p.write_text("print('hello')\n", encoding="utf-8")
        cp = json.loads(self.candidate_project.read_text())
        cp["tree"]["ServerScriptService"]["RogueGame"] = {"$path": p.name}
        self.candidate_project.write_text(json.dumps(cp), encoding="utf-8")
        self.assertIn("lacks owner-scoped overlay", " ".join(self.run_check()["errors"]))

    def test_duplicate_path_disallowed(self):
        cp = json.loads(self.candidate_project.read_text())
        cp["tree"]["ServerScriptService"]["DuplicateRules"] = {
            "$path": "EGGRUMBLE_CastleMatchRules.luau"
        }
        self.candidate_project.write_text(json.dumps(cp), encoding="utf-8")
        self.assertIn("duplicate source", " ".join(self.run_check()["errors"]))

    def test_path_traversal_disallowed(self):
        cp = json.loads(self.candidate_project.read_text())
        cp["tree"]["ServerScriptService"]["EGGRUMBLE_CastleMatchRules"] = {
            "$path": "../author/EGGRUMBLE_CastleMatchRules.luau"
        }
        self.candidate_project.write_text(json.dumps(cp), encoding="utf-8")
        self.assertIn("escaping source", " ".join(self.run_check()["errors"]))

    def test_extra_game_owner_is_rejected_even_with_overlay(self):
        cp = json.loads(self.candidate_project.read_text())
        cp["tree"]["ServerScriptService"]["Game"] = {"$path": "Game.server.luau"}
        (self.candidate / "Game.server.luau").write_text("print('bad')\n")
        self.candidate_project.write_text(json.dumps(cp), encoding="utf-8")
        self.assertIn("multiple match owners", " ".join(self.run_check()["errors"]))

    def test_server_client_swap_rejected(self):
        cp = json.loads(self.candidate_project.read_text())
        n = cp["tree"]["StarterPlayer"]["StarterPlayerScripts"].pop(
            "EGGRUMBLE_CombatFeel"
        )
        cp["tree"]["ServerScriptService"]["EGGRUMBLE_CombatFeel"] = n
        self.candidate_project.write_text(json.dumps(cp), encoding="utf-8")
        out = self.run_check()
        self.assertIn("client script is on server", " ".join(out["errors"]))

    def test_missing_overlay_owner_and_rollback_rejected(self):
        name = "EGGRUMBLE_BotActors"
        f = self.candidate / (name + ".luau")
        f.write_text("return { changed=true }")
        self.provenance["overlays"][name] = {
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
            "original_sha256": hashlib.sha256((self.author / f.name).read_bytes()).hexdigest(),
            "feature_id": "AI"
        }
        out = self.run_check()
        self.assertIn("requires owner", " ".join(out["errors"]))
        self.assertIn("requires rollback", " ".join(out["errors"]))

    def test_unjustified_manifest_claim_rejected(self):
        name = "EGGRUMBLE_BotActors"
        self.provenance["overlays"][name] = {
            "owner": "#484", "feature_id": "AI", "reason": "none",
            "rollback": "sha", "sha256": "0" * 64}
        self.assertIn("declared overlay without actual change", " ".join(self.run_check()["errors"]))



    def test_unapproved_author_source_replacement_is_rejected_even_with_manifest(self):
        name = "EGGRUMBLE_CastleMatchRules"
        source = self.candidate / (name + ".luau")
        original_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        source.write_text("return { cheating=true }\n")
        self.provenance["overlays"][name] = {
            "owner": "#482", "feature_id": "CASTLE", "reason": "attempted fork",
            "rollback": original_sha, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "original_sha256": original_sha
        }
        self.assertIn("owner has no approved", " ".join(self.run_check()["errors"]))

    def test_wrong_overlay_owner_fails(self):
        name = "EGGRUMBLE_BotActors"
        source = self.candidate / (name + ".luau")
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        source.write_text("return { repaired=true }\n")
        self.provenance["overlays"][name] = {
            "owner": "#487", "feature_id": "AI", "reason": "owner collision",
            "rollback": before, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "original_sha256": before
        }
        self.assertIn("unauthorized owner", " ".join(self.run_check()["errors"]))

    def test_source_remap_across_safe_checkouts_preserves_bytes(self):
        # Real #484 composed manifest uses paths outside artifacts but inside a
        # checkout root; compare class + bytes, not relative $path string.
        cp = json.loads(self.candidate_project.read_text())
        dst = self.candidate / "checked_out_original"
        dst.mkdir()
        name = "EGGRUMBLE_SevenRoleCombat"
        path = name + ".luau"
        (dst / path).write_bytes((self.candidate / path).read_bytes())
        cp["tree"]["ServerScriptService"][name] = {"$path": "checked_out_original/" + path}
        self.candidate_project.write_text(json.dumps(cp), encoding="utf-8")
        self.assertEqual(self.run_check()["status"], "SOURCE_GATE_PASS")

    def test_composite_requires_all_four_artist_scripts_plus_score(self):
        extra = "EGGRUMBLE_ScoreBalance"
        cp = json.loads(self.candidate_project.read_text())
        (self.candidate / (extra + ".luau")).write_text("return {}\n")
        cp["tree"]["ServerScriptService"][extra] = {"$path": extra + ".luau"}
        self.candidate_project.write_text(json.dumps(cp), encoding="utf-8")
        self.assertIn("incomplete or unknown 26-source", " ".join(self.run_check()["errors"]))

    def test_reject_second_game_host_even_with_claim(self):
        cp = json.loads(self.candidate_project.read_text())
        cp["tree"]["ServerScriptService"]["SecondGame"] = {"$path": "SecondGame.server.luau"}
        (self.candidate / "SecondGame.server.luau").write_text("print('bad')\n")
        self.candidate_project.write_text(json.dumps(cp), encoding="utf-8")
        self.assertIn("second unapproved server Script", " ".join(self.run_check()["errors"]))

    def test_full_26_source_original_art_score_owner_manifest_passes(self):
        cp = json.loads(self.candidate_project.read_text())
        new = {
            "EGGRUMBLE_HeroSilhouetteArt": ("#485", ".server.luau"),
            "EGGRUMBLE_FlagshipFieldArt": ("#485", ".server.luau"),
            "EGGRUMBLE_EncounterReadabilityArt": ("#485", ".server.luau"),
            "EGGRUMBLE_ArtDistanceLOD": ("#485", ".client.luau"),
            "EGGRUMBLE_ScoreBalance": ("#487", ".luau"),
        }
        for name, (owner, suffix) in new.items():
            path = name + suffix
            source = self.candidate / path
            source.write_text("return {}\n", encoding="utf-8")
            if suffix == ".client.luau":
                service = cp["tree"]["StarterPlayer"]["StarterPlayerScripts"]
            else:
                service = cp["tree"]["ServerScriptService"]
            service[name] = {"$path": path}
            self.provenance["overlays"][name] = {
                "owner": owner, "feature_id": "SOURCE-" + owner, "reason": "original owner reuse",
                "rollback": "remove exact module",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest()
            }
        self.provenance["expected_candidate_sources"] = 26
        self.candidate_project.write_text(json.dumps(cp), encoding="utf-8")
        outcome = self.run_check()
        self.assertEqual(outcome["status"], "SOURCE_GATE_PASS", outcome["errors"])
        self.assertEqual(outcome["source_count_candidate"], 26)

if __name__ == "__main__":
    unittest.main()
