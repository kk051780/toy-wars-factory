"""EGGRUMBLE real-hit audio: original 21-source lineage and pure-local authority checks."""
import json
import re
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
REPO=HERE.parents[1]
ORIGINAL=REPO/"handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_V3_STUDIO.project.json"
SOURCE=HERE/"EGGRUMBLE_RealHitAudio.client.luau"
PROJECT=HERE/"EGGRUMBLE_V3_AUDIO_STUDIO.project.json"

def paths(node):
    if isinstance(node,dict):
        if "$path" in node:
            yield node["$path"]
        else:
            for key,value in node.items():
                if not key.startswith("$"):
                    yield from paths(value)

class AudioContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=SOURCE.read_text(encoding="utf-8")
        cls.base=json.loads(ORIGINAL.read_text(encoding="utf-8"))
        cls.project=json.loads(PROJECT.read_text(encoding="utf-8"))
    def test_reuse_all_21_original_files_without_copying(self):
        originals=list(paths(self.base["tree"]))
        candidate=list(paths(self.project["tree"]))
        self.assertEqual(21,len(originals))
        self.assertEqual(22,len(candidate))
        paths_real={(PROJECT.parent/p).resolve(strict=True) for p in candidate}
        for p in originals:
            self.assertIn((ORIGINAL.parent/p).resolve(strict=True),paths_real)
        self.assertIn(SOURCE.resolve(strict=True),paths_real)
    def test_one_optional_client_no_game_authority(self):
        client=self.project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertEqual({"EGGRUMBLE_CombatFeel","EGGRUMBLE_ProceduralSkills","EGGRUMBLE_RealHitAudio"},set(client))
        self.assertEqual("EGGRUMBLE_RealHitAudio.client.luau",client["EGGRUMBLE_RealHitAudio"]["$path"])
        for prohibited in ("RemoteEvent","TakeDamage(","SetAttribute(","DataStoreService",
                           "Humanoid.WalkSpeed","Tool.Activated","Touched:Connect"):
            self.assertNotIn(prohibited,self.source)
    def test_cannot_play_on_miss_death_or_audio_mute(self):
        for token in ('GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")',
                      '"EGGRUMBLE_ImpactRole"','"EGGRUMBLE_ImpactSlot"',
                      '"EGGRUMBLE_ImpactWeight"','"EGGRUMBLE_SFXMuted"',
                      '"EGGRUMBLE_Eliminated"','humanoid.Health>0',
                      'lastSequence=sequence'):
            self.assertIn(token,self.source)
        self.assertIn('if not RunService:IsStudio() then return end',self.source)
    def test_seven_roles_and_sound_cap(self):
        roles=[name for name in ("WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE") if f"{name}={{id=" in self.source]
        self.assertEqual(7,len(roles))
        self.assertEqual(7,len(set(roles)))
        self.assertEqual(7,self.source.count('id="rbxasset://sounds/'))
        self.assertIn('local MAX_PER_WINDOW=6',self.source)
        self.assertIn('local MAX_VOICES=4',self.source)
        self.assertIn('local MAX_VOLUME=.30',self.source)
        self.assertIn('if SoundService:FindFirstChild(GROUP) then',self.source)

if __name__=="__main__":
    unittest.main()
