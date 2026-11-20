"""SOURCE-level guardrails for EGGRUMBLE V2 mass-battle preview; not Roblox engine proof."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PREVIEW=ROOT / "EGGRUMBLE_MassBattleCastlePreview.server.luau"
HERO=ROOT / "SevenHeroArena.server.luau"
SPEC=ROOT / "EGGRUMBLE_V2_MASS_BATTLE_PERSONAL_CASTLE_CONTRACT.md"

class EGGRUMBLEMassBattleContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview=PREVIEW.read_text(encoding="utf-8")
        cls.hero=HERO.read_text(encoding="utf-8")
        cls.spec=SPEC.read_text(encoding="utf-8")

    def test_bushin_only_display_name_and_internal_role_unchanged(self):
        self.assertIn('WARRIOR={name="武神"', self.hero)
        self.assertNotIn('WARRIOR={name="神将（仮）"', self.hero)
        for name in ("WarGodFlyingSlash","P0DPreviewKami","OrochiDivineHead_",
                     "P0DPreviewWarlordStance","if num==1 then"):
            self.assertIn(name,self.hero)

    def test_playable_sector_coverage_and_capped_real_enemies(self):
        for value in ("MAP_TILE=460","GRID=3","for i=1,9 do","MAX_NEUTRAL_LIVE=96",
                      "MAX_SPAWN_PER_TICK=4","SPAWN_INTERVAL=.12",
                      "RESPAWN_DELAY=.55","PER_ATTACK_CAP=28"):
            with self.subTest(value=value):
                self.assertIn(value,self.preview)
        self.assertIn('h.Died:Connect(function()',self.preview)
        self.assertIn('target:SetAttribute("LastAttackerUserId",player.UserId)',self.preview)
        self.assertIn('GetPlayerByUserId(uid)',self.preview)
        self.assertIn('updateProgress(who,1)',self.preview)
        self.assertNotIn('updateProgress(who,1000)',self.preview)

    def test_each_player_gets_owned_customizable_castle_and_team(self):
        for value in ("playerCastles[player.UserId]=model",
                      'model:SetAttribute("CastleOwnerUserId",player.UserId)',
                      "playerCastleSlots[player.UserId]=slot",
                      'prompt.ActionText="装飾を変更"',
                      "if actor.UserId~=player.UserId then return end",
                      "player.Team",'"EGGRUMBLE\\n"..player.DisplayName.." の城"'):
            with self.subTest(value=value):
                self.assertIn(value,self.preview)

    def test_server_authority_and_nonproduction_guard(self):
        self.assertIn("if not RunService:IsStudio() then return end",self.preview)
        for forbidden in ("DataStoreService","RemoteEvent","TeleportService",
                          "MarketplaceService","PublishAsync","HTTPService"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden,self.preview)
        self.assertIn("source-confirmed",self.spec) if "source-confirmed" in self.spec else self.assertIn("server-owned death attribution",self.spec)
        self.assertIn("10,000+",self.spec)
        self.assertIn("30,000+",self.spec)
        self.assertIn("EGGRUMBLE",self.spec)
        self.assertIn("SOURCE_WIP",self.spec)

    def test_battle_progression_and_auto_basic(self):
        for token in ("EGGRUMBLE_NeutralKOs","EGGRUMBLE_RunRank","EGGRUMBLE_SlashTier",
                      "TEMPEST","WAVE","CONFIG.AUTO_INTERVAL",
                      't.Name="EGGRUMBLE_武神の飛翔斬撃"'):
            with self.subTest(token=token):
                self.assertIn(token,self.preview)

if __name__=="__main__":
    unittest.main()
