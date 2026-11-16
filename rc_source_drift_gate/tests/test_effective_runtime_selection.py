"""Verify which original-owner code actually executes in a composed 26-source Place.

The old author-only guard scan could miss or invent real release blockers when
#484 replaces BotActors and #487 replaces MatchResultService. Network-free
negative tests cover overlay owner selection, generated-host ancestry and
release gating. Real GitHub API HEAD tests run separately in CI.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_live_intake import (
    PROJECT, HOST_GUARD, HOST_RAMP_ANCHOR,
    select_current26_runtime_sources,
)
from runtime_activation import REQUIRED_RUNTIME_SOURCES, evaluate_runtime_activation


def prep():
    project = {
        "tree": {
            "ServerScriptService": {"$className": "ServerScriptService"},
            "StarterPlayer": {"StarterPlayerScripts": {"$className": "StarterPlayerScripts"}}
        }
    }
    for n in REQUIRED_RUNTIME_SOURCES:
        project["tree"]["ServerScriptService"][n] = {"$path": n + (
            ".server.luau" if n == "EGGRUMBLE_LobbyCastleModesPreview"
            else ".luau")}
    heads = {role: role[0] * 40 for role in ("author", "quality", "score", "art")}
    prs = {role: {"head": {"sha": sha}} for role, sha in heads.items()}
    composer = (
        "def apply_ramp(author_source,quality_source):\n"
        "    return author_source.replace(end,ramp+\"\\n\"+end)\n"
        "for name in (\"EGGRUMBLE_BotActors\",\"EGGRUMBLE_BotPathRouter\"):\n"
        "    server[name]=source_path(out,src)\n"
        "server[\"EGGRUMBLE_MatchResultService\"]=source_path(out,result)\n"
    )
    calls = []
    prefix = str(Path(PROJECT).parent).replace("\\", "/")
    def fake(path,sha):
        calls.append((path,sha))
        if path == prefix + "/EGGRUMBLE_LobbyCastleModesPreview.server.luau":
            return "local RunService = game:GetService('RunService')\n" + HOST_GUARD + "\n" + HOST_RAMP_ANCHOR + "\n"
        if path == prefix + "/EGGRUMBLE_BotActors.luau":
            return "assert(RunService:IsStudio(), 'GQ quality version')\n" if sha==heads["quality"] else "return {}"
        if path == prefix + "/EGGRUMBLE_MatchResultService.luau":
            return "assert(RunService:IsStudio(), 'SCORE author version')\n" if sha==heads["score"] else "return {}"
        return "return {}\n"
    return prs,project,composer,fake,calls,heads


class EffectiveRuntimeSelectionTest(unittest.TestCase):
    def test_uses_actual_quality_bot_and_score_overrides_not_author_head(self):
        prs,project,composer,fake,calls,heads=prep()
        src,selection=select_current26_runtime_sources(prs,project,composer,fake)
        self.assertEqual(len(src),len(REQUIRED_RUNTIME_SOURCES))
        self.assertEqual(selection["EGGRUMBLE_BotActors"]["selected_owner"],"quality")
        self.assertEqual(selection["EGGRUMBLE_MatchResultService"]["selected_owner"],"score")
        self.assertEqual(selection["EGGRUMBLE_BotActors"]["selected_commit"],heads["quality"])
        self.assertEqual(selection["EGGRUMBLE_MatchResultService"]["selected_commit"],heads["score"])
        self.assertEqual(evaluate_runtime_activation(src)["production_runtime"],"BLOCKED_STUDIO_ONLY_GAME_HOST")
        self.assertEqual(evaluate_runtime_activation(src)["guard_count"],3)

    def test_exact_host_prefix_is_required_and_generated_byte_claim_prohibited(self):
        prs,project,composer,fake,_,_=prep()
        _,p=select_current26_runtime_sources(prs,project,composer,fake)
        self.assertEqual(p["EGGRUMBLE_LobbyCastleModesPreview"]["assembled_host_sha256"],"NOT_CLAIMED")
        self.assertEqual(p["EGGRUMBLE_LobbyCastleModesPreview"]["evidence_region"],
                         "AUTHOR_HOST_PREFIX_BEFORE_COMPOSER_RAMP")

    def test_untrusted_composer_overrides_fail_closed(self):
        prs,project,composer,fake,_,_=prep()
        composer=composer.replace("server[name]=source_path(out,src)", "server[name]=UNTRUSTED_GAME")
        with self.assertRaisesRegex(ValueError,"current26_runtime_overlay_untrusted"):
            select_current26_runtime_sources(prs,project,composer,fake)

    def test_guard_after_generated_castle_anchor_is_not_proven_unchanged(self):
        prs,project,composer,fake,_,_=prep()
        def bad(path,sha):
            x=fake(path,sha)
            if path.endswith("EGGRUMBLE_LobbyCastleModesPreview.server.luau"):
                return HOST_RAMP_ANCHOR + "\n" + HOST_GUARD + "\n"
            return x
        with self.assertRaisesRegex(ValueError,"host_guard_not_in_untouched_prefix"):
            select_current26_runtime_sources(prs,project,composer,bad)

    def test_missing_runtime_module_fails_closed(self):
        prs,project,composer,fake,_,_=prep()
        del project["tree"]["ServerScriptService"]["EGGRUMBLE_BotActors"]
        with self.assertRaisesRegex(ValueError,"runtime_module_missing"):
            select_current26_runtime_sources(prs,project,composer,fake)

    def test_unpinned_untrusted_source_is_not_allowed(self):
        prs,project,composer,fake,_,_=prep()
        def empty(path,sha):
            if path.endswith("EGGRUMBLE_BotActors.luau"):
                return None
            return fake(path,sha)
        with self.assertRaisesRegex(ValueError,"empty_runtime_source"):
            select_current26_runtime_sources(prs,project,composer,empty)

    def test_clean_author_shadow_does_not_hide_quality_studio_guard(self):
        prs,project,composer,fake,_,heads=prep()
        # Regression: author BotActors content is clean but quality's effective
        # overlay is guarded. Scanning only the author would be a false pass.
        prefix=str(Path(PROJECT).parent).replace("\\","/")
        self.assertEqual(fake(prefix+"/EGGRUMBLE_BotActors.luau",heads["author"]),"return {}")
        src,_=select_current26_runtime_sources(prs,project,composer,fake)
        self.assertIn("IsStudio()",src["EGGRUMBLE_BotActors"])


if __name__=="__main__":
    unittest.main()
