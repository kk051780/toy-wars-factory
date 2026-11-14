"""FB015 P0 motion: all four complete character art silhouettes must follow Core.

Static source + actual author enumeration contract. Roblox Studio/Android visual
acceptance remains necessary; do not claim this proves a rendering frame.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parent
MOTION=ROOT/"features/art_motion/NeutralMotion.client.luau"
AUTHOR=ROOT/"features/art_minion/MinionArtSilhouette.server.luau"

EXPECTED={
    "KNIGHT":{
        "ART_KNIGHT_CHEST","ART_KNIGHT_HELMET","ART_KNIGHT_CREST",
        "ART_KNIGHT_PAULDRON_-1","ART_KNIGHT_PAULDRON_1",
        "ART_KNIGHT_SHIELD","ART_KNIGHT_SHIELD_MARK",
        "ART_KNIGHT_SPEAR_SHAFT","ART_KNIGHT_SPEAR_TIP","ART_KNIGHT_CAPE",
    },
    "WRAITH":{
        "ART_WRAITH_HOOD","ART_WRAITH_COWL","ART_WRAITH_FACE_VEIL",
        "ART_WRAITH_CRYSTAL_EYE_-1","ART_WRAITH_CRYSTAL_EYE_1",
        "ART_WRAITH_SHOULDER_FIN_-1","ART_WRAITH_SHOULDER_FIN_1",
        "ART_WRAITH_CHEST_SIGIL","ART_WRAITH_ORB","ART_WRAITH_SHROUD",
    },
    "BRUTE":{
        "ART_BRUTE_CHEST_PLATE","ART_BRUTE_JAW",
        "ART_BRUTE_TUSK_-1","ART_BRUTE_TUSK_1",
        "ART_BRUTE_HORN_-1","ART_BRUTE_HORN_1",
        "ART_BRUTE_SHOULDER_-1","ART_BRUTE_SHOULDER_1",
        "ART_BRUTE_MAUL_HANDLE","ART_BRUTE_MAUL_HEAD","ART_BRUTE_BACK_FUR",
    },
    "ELITE":{
        "ART_ELITE_CHEST_ARMOUR","ART_ELITE_MASK",
        "ART_ELITE_CURVED_HORN_-1","ART_ELITE_CURVED_HORN_1",
        "ART_ELITE_SHOULDER_SPIKE_-1","ART_ELITE_SHOULDER_SPIKE_1",
        "ART_ELITE_GAUNTLET_-1","ART_ELITE_GAUNTLET_1",
        "ART_ELITE_BACK_BANNER","ART_ELITE_WAR_CORE",
    },
}

def source_set(source):
    block=source.split("local watchedParts = {",1)[1].split("\n}\n",1)[0]
    found={}
    for kind in EXPECTED:
        match=re.search(r"(?ms)^    "+kind+r" = \{(.*?)^    \},",block)
        assert match, ("MISSING_WATCHED_KIND",kind)
        found[kind]=set(re.findall(r'"(ART_[A-Z_0-9-]+)"',match.group(1)))
        assert len(found[kind])==len(re.findall(r'"(ART_[A-Z_0-9-]+)"',match.group(1)))
    return found

class FullSilhouetteFollowing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.motion=MOTION.read_text("utf8")
        cls.author=AUTHOR.read_text("utf8")

    def test_all_41_existing_parts_attached_without_omission(self):
        actual=source_set(self.motion)
        self.assertEqual(actual,EXPECTED)
        self.assertEqual(sum(map(len,actual.values())),41)

    def test_all_parts_originated_in_actual_character_author(self):
        for kind,names in EXPECTED.items():
            for name in names:
                base=name.removeprefix("ART_")
                if base.endswith("_-1") or base.endswith("_1"):
                    base=base.rsplit("_",1)[0]+"_"
                self.assertIn('"'+base,self.author, (kind,name))

    def test_nine_models_full_costume_budget(self):
        total=3*len(EXPECTED["KNIGHT"])+3*len(EXPECTED["WRAITH"])+2*len(EXPECTED["BRUTE"])+len(EXPECTED["ELITE"])
        self.assertEqual(total,92)
        maxparts=int(re.search(r"local MAX_ACTIVE_COSMETIC_PARTS = (\d+)",self.motion).group(1))
        self.assertGreaterEqual(maxparts,total)
        self.assertLessEqual(maxparts,112,"mobile budget should stay bounded")
        self.assertIn("MAX_MODELS = 16",self.motion)
        self.assertIn("ANIM_STEP = 1 / 25",self.motion)
        self.assertIn("VIEW_RANGE_STUDS = 105",self.motion)

    def test_render_all_originals_through_local_clones(self):
        for anchor in ('local copy = source:Clone()',
                       'copy.Parent = localArt',
                       'core.CFrame:ToObjectSpace(source.CFrame)',
                       'visual.copy.CFrame = core.CFrame * visual.offset * localMotion'):
            self.assertIn(anchor,self.motion)
        self.assertNotIn('visual.original.CFrame =',self.motion)
        self.assertNotIn('Instance.new("Part")',self.motion)

    def test_out_of_range_never_resurrects_anchored_spawn_ghosts(self):
        self.assertIn('original.LocalTransparencyModifier = visual.initialModifier',self.motion)
        tail=self.motion.split('                -- IMPORTANT: hiding out-of-range clones',1)[1]
        block=tail.split('    end\nend)',1)[0]
        self.assertIn('visual.original.LocalTransparencyModifier = 1',block)
        self.assertIn('visual.copy.Transparency = 1',block)
        self.assertNotIn('visual.initialModifier',block)

    def test_immediate_first_frame_hides_spawn_ghosts(self):
        start=self.motion.index('    activeParts += #attachments')
        end=self.motion.index('    return true',start)
        self.assertIn('visual.original.LocalTransparencyModifier = 1',self.motion[start:end])

    def test_no_authority_or_second_game(self):
        for prohibited in ('TakeDamage(', 'FireServer(', 'OnServerEvent:',
                           'DataStoreService', 'Instance.new("RemoteEvent")',
                           'MarketplaceService', 'UpdateAsync('):
            self.assertNotIn(prohibited,self.motion)
        self.assertIn('if not RunService:IsStudio() then return end',self.motion)

if __name__=="__main__":unittest.main()
