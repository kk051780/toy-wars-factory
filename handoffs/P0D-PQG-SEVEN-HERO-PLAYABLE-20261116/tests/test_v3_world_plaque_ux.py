"""GQ539 lobby-only visual safety. Castle/vault boards belong to existing PR #547.

This source-only contract proves no duplicate UI authority, no original core edits,
and a reversible four-call-site label cleanup. Studio/Android still untested.
"""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
SRC = SOURCE.read_text(encoding="utf-8")
ORIGINAL = '''local function board(at:BasePart,label:string)
 local b=Instance.new("BillboardGui");b.Size=UDim2.fromOffset(230,82);b.StudsOffset=Vector3.new(0,4.5,0)
 b.AlwaysOnTop=true;b.Parent=at
 local t=Instance.new("TextLabel");t.Size=UDim2.fromScale(1,1);t.TextScaled=true;t.TextWrapped=true
 t.BackgroundColor3=Color3.fromRGB(24,27,43);t.BackgroundTransparency=.12
 t.TextColor3=Color3.new(1,1,1);t.Font=Enum.Font.GothamBold;t.Text=label;t.Parent=b
end'''


def block(source, function_name):
    begin = source.index("local function " + function_name + "(")
    end = source.index("\nlocal function ", begin + 1)
    return source[begin:end].strip()


def nearby_is_safe(source):
    helper = block(source, "nearbyBoard")
    return all(x in helper for x in (
        "board(at,label)",
        'at:FindFirstChildOfClass("BillboardGui")',
        "gui.AlwaysOnTop=false",
        "gui.MaxDistance=math.clamp(maxDistance,16,52)",
        "gui.Size=UDim2.fromOffset(174,56)",
        "gui.StudsOffsetWorldSpace=Vector3.new(0,3.2,0)",
        "title.TextScaled=false",
        "title.TextSize=14",
        "title.BackgroundTransparency=.54",
    )) and "Instance.new" not in helper


class TestLobbyOnlyBillboards(unittest.TestCase):
    def test_castle_and_egg_original_board_factory_kept_exact(self):
        self.assertEqual(block(SRC, "board"), ORIGINAL)

    def test_castle_egg_calls_left_to_original_547(self):
        self.assertIn('board(core,(entry.isAI and "AI " or "")..entry.id.." の城\\n卵×3 / HP1000")', SRC)
        self.assertIn('board(vault,"卵倉庫")', SRC)
        self.assertNotIn("coreBoard.AlwaysOnTop=false", SRC)
        self.assertNotIn("vaultBoard.AlwaysOnTop=false", SRC)

    def test_only_four_local_role_mode_defense_labels_switch(self):
        anchors = (
            'nearbyBoard(stand,data.name.."\\n"..data.weapon,24)',
            'nearbyBoard(gateTeam,"EGGRUMBLE\\nチーム戦｜全味方城陥落で敗北",44)',
            'nearbyBoard(gateBR,"EGGRUMBLE\\nバトルロワイヤル｜最後の城が勝者",44)',
            'nearbyBoard(stand,name.."\\n出撃前の防衛選択",25)',
        )
        for anchor in anchors:
            self.assertIn(anchor, SRC)
        self.assertEqual(SRC.count("nearbyBoard("), 5)  # declaration plus four uses

    def test_labels_reuse_existing_gui_and_are_occluded_nearby(self):
        self.assertTrue(nearby_is_safe(SRC))
        self.assertEqual(block(SRC,"nearbyBoard").count("board(at,label)"),1)

    def test_mutant_unbounded_distance_rejected(self):
        self.assertFalse(nearby_is_safe(SRC.replace(
            "gui.MaxDistance=math.clamp(maxDistance,16,52)","gui.MaxDistance=0"
        )))

    def test_mutant_always_on_top_rejected(self):
        self.assertFalse(nearby_is_safe(SRC.replace(
            "gui.AlwaysOnTop=false","gui.AlwaysOnTop=true"
        )))

    def test_original_hp_and_egg_update_remains_single_server(self):
        self.assertIn('bits.core:FindFirstChildOfClass("BillboardGui")', SRC)
        self.assertIn("math.floor(c.hp)", SRC)
        self.assertIn("c.vaultEggs", SRC)
        self.assertIn("Rules.depositEggs(", SRC)
        self.assertIn("Rules.takeEggs(", SRC)

    def test_no_new_authority_or_extraneous_ui_instances(self):
        self.assertEqual(SRC.count('Instance.new("BillboardGui")'),1)
        self.assertNotIn('Instance.new("RemoteEvent")', SRC)
        self.assertNotIn("DataStoreService", SRC)
        self.assertNotIn("MarketplaceService", SRC)


if __name__ == "__main__":
    unittest.main()
