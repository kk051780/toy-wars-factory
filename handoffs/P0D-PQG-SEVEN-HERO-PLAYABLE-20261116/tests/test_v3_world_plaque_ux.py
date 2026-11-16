"""GQ-V3: original V3 world labels cannot obscure combat, eggs, or castle routes.

Static source acceptance only; Studio camera and Android visibility remain unverified.
The negative fixtures check that the gate fails on the original unbounded design.
"""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
SRC = SOURCE.read_text(encoding="utf-8")


def safe_board(source: str) -> bool:
    begin = source.index("local function board(")
    end = source.index("\nlocal function prompt(", begin)
    body = source[begin:end]
    return all(
        token in body for token in (
            "b.AlwaysOnTop=false",
            "b.MaxDistance=math.clamp(maxDistance or 42,16,52)",
            "t.TextScaled=false",
            "t.TextSize=14",
            "t.BackgroundTransparency=.54",
            "b.StudsOffsetWorldSpace=",
        )
    ) and "b.AlwaysOnTop=true" not in body


class TestNearbyPlaqueSafety(unittest.TestCase):
    def test_original_world_plaques_are_occluded_and_distance_bounded(self):
        self.assertTrue(safe_board(SRC))

    def test_regression_always_on_top_is_rejected(self):
        self.assertFalse(safe_board(SRC.replace("b.AlwaysOnTop=false", "b.AlwaysOnTop=true")))

    def test_regression_unlimited_distance_is_rejected(self):
        self.assertFalse(safe_board(SRC.replace(
            "b.MaxDistance=math.clamp(maxDistance or 42,16,52)", "b.MaxDistance=0"
        )))

    def test_distance_limits_are_for_lobby_castle_roles_and_eggs(self):
        for anchor in (
            'board(core,(entry.isAI and "AI " or "")',
            'board(vault,"卵倉庫",28)',
            'board(stand,data.name.."\\n"..data.weapon,24)',
            'board(gateTeam,"EGGRUMBLE\\nチーム戦｜全味方城陥落で敗北",44)',
            'board(gateBR,"EGGRUMBLE\\nバトルロワイヤル｜最後の城が勝者",44)',
            'board(stand,name.."\\n出撃前の防衛選択",25)',
        ):
            self.assertIn(anchor, SRC)

    def test_castle_hp_egg_values_still_refresh(self):
        # Pure visual patch must preserve live server-backed HP and egg numbers.
        self.assertIn('bits.core:FindFirstChildOfClass("BillboardGui")', SRC)
        self.assertIn('math.floor(c.hp)', SRC)
        self.assertIn('c.vaultEggs', SRC)

    def test_no_new_remote_game_or_shop_authority(self):
        self.assertNotIn('Instance.new("RemoteEvent")', SRC)
        self.assertNotIn('DataStoreService', SRC)
        self.assertNotIn('MarketplaceService', SRC)


if __name__ == "__main__":
    unittest.main()
