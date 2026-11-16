"""27??? No: actual selection must be exactly 21+4+1=26.

All tests run without GitHub network or Roblox engines. This is a read-only
runtime guard auditor, not duplicated 26-source composer or 7-role gameplay.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_live_intake import PROJECT, project_nodes
from full26_runtime import (
    ART, GAME, ART_SCRIPT_FILES, ALL_DOMAINS,
    inspect_full26_runtime, select_all26_runtime_sources,
)
from runtime_activation import REQUIRED_RUNTIME_SOURCES


ORIGINAL = [
    "CastleMatchRules","BotPathRouter","BotActors","SwarmCombat",
    "LobbyCastleModesPreview","InteractionGuard","SevenRoleCombat",
    "MatchResultService","CombatBalance","SkillFX","RoundReplay",
    "AttackGeometry","ImpactFeedback","WeaponSilhouettes","DivineMantle",
    "FieldItemPickups","RaidItemIntake","NeutralStoneGiant",
    "BossSessionFence","CombatFeel","ProceduralSkills",
]


def fixture():
    tree={"ServerScriptService":{"$className":"ServerScriptService"},
          "StarterPlayer":{"StarterPlayerScripts":{"$className":"StarterPlayerScripts"}}}
    for suffix in ORIGINAL:
        name="EGGRUMBLE_"+suffix
        ext=(".server.luau" if suffix=="LobbyCastleModesPreview" else
             ".client.luau" if suffix in ("CombatFeel","ProceduralSkills") else ".luau")
        group=(tree["StarterPlayer"]["StarterPlayerScripts"]
               if suffix in ("CombatFeel","ProceduralSkills") else tree["ServerScriptService"])
        group[name]={"$path":name+ext}
    author={"tree":tree}
    head={k:k[0]*40 for k in ("author","quality","score","art")}
    prs={k:{"head":{"sha":v}} for k,v in head.items()}
    calls=[]
    prefix=str(Path(PROJECT).parent).replace("\\","/")
    def reader(path, sha):
        calls.append((path,sha))
        if path.startswith(ART):
            return "-- visual\nif not RunService:IsStudio() then return end\n"
        if path==prefix+"/EGGRUMBLE_LobbyCastleModesPreview.server.luau":
            return "local x=1\nif not RunService:IsStudio() then return end\n"
        if path==prefix+"/EGGRUMBLE_BotActors.luau" and sha==head["quality"]:
            return "assert(RunService:IsStudio(),'actual selected quality bot')\n"
        if path==prefix+"/EGGRUMBLE_MatchResultService.luau" and sha==head["score"]:
            return "assert(RunService:IsStudio(),'actual selected score')\n"
        return "return {}\n"
    def choose_five(prs,project,composer,read_pinned):
        src={}
        prov={}
        for name in REQUIRED_RUNTIME_SOURCES:
            owner=("quality" if name=="EGGRUMBLE_BotActors" else
                   "score" if name=="EGGRUMBLE_MatchResultService" else "author")
            sha=prs[owner]["head"]["sha"]
            path=project_nodes(project)[name]["path"]
            src[name]=read_pinned(path,sha)
            prov[name]={"selected_owner":owner,"selected_commit":sha,
                        "path":path,"evidence_region":"STUB"}
        return src,prov
    return prs,author,choose_five,reader,calls,head


class Full26RuntimeInspectionTest(unittest.TestCase):
    def test_real26_authored_source_selection_and_four_visual_guards(self):
        prs,author,chooser,reader,calls,head=fixture()
        src,orig=select_all26_runtime_sources(prs,author,"",project_nodes,chooser,reader)
        result=inspect_full26_runtime(src,orig)
        self.assertEqual(result["selected_script_count"],26)
        self.assertEqual(result["art_guard_count"],4)
        self.assertEqual(result["game_guard_count"],3)
        self.assertEqual(result["guard_count"],7)
        self.assertEqual(result["gameplay_server_activation"],"BLOCKED_PREVIEW_HOST")
        self.assertEqual(result["art_nonstudio_visual_activation"],"STUDIO_ONLY_VISUALS_DETECTED")
        self.assertEqual(tuple(result["per_domain"]),ALL_DOMAINS)
        self.assertFalse(result["product_go"])

    def test_all_four_art_author_commit_is_original_not_game_clone(self):
        prs,author,chooser,reader,calls,head=fixture()
        src,orig=select_all26_runtime_sources(prs,author,"",project_nodes,chooser,reader)
        for art in ART_SCRIPT_FILES:
            self.assertEqual(orig[art]["selected_owner"],"art")
            self.assertEqual(orig[art]["selected_commit"],head["art"])
            self.assertIn((orig[art]["path"],head["art"]),calls)
        self.assertEqual(orig["EGGRUMBLE_ScoreBalance"]["selected_commit"],head["score"])
        self.assertEqual(orig["EGGRUMBLE_BotPathRouter"]["selected_commit"],head["quality"])

    def test_visual_guard_does_not_fake_loss_of_score_balance(self):
        prs,author,chooser,reader,calls,head=fixture()
        src,orig=select_all26_runtime_sources(prs,author,"",project_nodes,chooser,reader)
        result=inspect_full26_runtime(src,orig)
        self.assertEqual(result["per_domain"]["balance"]["art_guard_count"],0)
        self.assertGreater(result["per_domain"]["character"]["art_guard_count"],0)
        self.assertTrue(result["generated_host_byte_identity"].startswith("NOT_ATTESTED"))

    def test_missing_art_is_fail_closed(self):
        prs,author,chooser,reader,calls,head=fixture()
        def missing(path,sha):
            if path.endswith("EGGRUMBLE_ArtDistanceLOD.client.luau"):
                return ""
            return reader(path,sha)
        with self.assertRaisesRegex(ValueError,"missing_selected_art_source"):
            select_all26_runtime_sources(prs,author,"",project_nodes,chooser,missing)

    def test_composite_schema_requires_21_author_sources(self):
        prs,author,chooser,reader,calls,head=fixture()
        author["tree"]["ServerScriptService"].pop("EGGRUMBLE_SkillFX")
        with self.assertRaisesRegex(ValueError,"author_is_not_21_sources"):
            select_all26_runtime_sources(prs,author,"",project_nodes,chooser,reader)

    def test_unclassified_new_script_is_not_silent_go(self):
        prs,author,chooser,reader,calls,head=fixture()
        src,orig=select_all26_runtime_sources(prs,author,"",project_nodes,chooser,reader)
        src["EGGRUMBLE_NotYetMapped"]="return {}\n"
        orig["EGGRUMBLE_NotYetMapped"]={"selected_owner":"author"}
        with self.assertRaisesRegex(ValueError,"incomplete_current26_source_selection"):
            inspect_full26_runtime(src,orig)

    def test_no_guards_is_still_not_production_approval(self):
        prs,author,chooser,reader,calls,head=fixture()
        src,orig=select_all26_runtime_sources(prs,author,"",project_nodes,chooser,reader)
        for name in src:
            src[name]="return {}\n"
        x=inspect_full26_runtime(src,orig)
        self.assertEqual(x["guard_count"],0)
        self.assertEqual(x["gameplay_server_activation"],
                         "NOT_VERIFIED_REQUIRES_REAL_NONSTUDIO_2CLIENT")
        self.assertEqual(x["art_nonstudio_visual_activation"],
                         "NOT_VERIFIED_REQUIRES_ANDROID_VISUAL_QA")
        self.assertFalse(x["product_go"])

    def test_duplicates_in_game_and_art_are_not_silently_accepted(self):
        prs,author,chooser,reader,calls,head=fixture()
        author["tree"]["ServerScriptService"]["EGGRUMBLE_ArtDistanceLOD"]={
            "$path":"EGGRUMBLE_ArtDistanceLOD.luau"}
        # There are now 22 original sources, not the owner's exact 21.
        with self.assertRaisesRegex(ValueError,"author_is_not_21_sources"):
            select_all26_runtime_sources(prs,author,"",project_nodes,chooser,reader)


if __name__=="__main__":
    unittest.main()
