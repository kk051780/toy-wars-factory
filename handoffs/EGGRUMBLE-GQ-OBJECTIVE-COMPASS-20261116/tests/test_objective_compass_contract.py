"""Source-exact, negative and ownership QA for the independent optional client objective cue."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent / "P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
SOURCE = ROOT / "EGGRUMBLE_ObjectiveCompass.client.luau"
PROJECT = ROOT / "EGGRUMBLE_GQ_OBJECTIVE_STUDIO.project.json"

def map_sources(node, prefix=()):
    out = {}
    for name, child in node.items():
        if name.startswith("$") or not isinstance(child, dict):
            continue
        key = prefix + (name,)
        if "$path" in child:
            out[key] = child["$path"]
        else:
            out.update(map_sources(child, key))
    return out

class CompassContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SOURCE.read_text(encoding="utf-8")
        cls.parent = map_sources(json.loads((PARENT / "EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8"))["tree"])
        cls.project = map_sources(json.loads(PROJECT.read_text(encoding="utf-8"))["tree"])

    def test_all_original_game_modules_stay_exactly_as_author_wired(self):
        self.assertEqual(len(self.parent), 21)
        self.assertEqual(len(self.project), 22)
        self.assertEqual(set(self.parent), set(self.project) - {
            ("StarterPlayer", "StarterPlayerScripts", "EGGRUMBLE_GQ_ObjectiveCompass")
        })
        for key, prior in self.parent.items():
            new_path = (ROOT / self.project[key]).resolve(strict=True)
            old_path = (PARENT / prior).resolve(strict=True)
            self.assertEqual(old_path, new_path, key)
        self.assertEqual(
            self.project[("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_GQ_ObjectiveCompass")],
            "EGGRUMBLE_ObjectiveCompass.client.luau")
        self.assertEqual(len({v for v in self.project.values()}), 22)

    def test_no_second_game_server_or_remote_authority(self):
        for forbidden in (
            "FireServer(", "InvokeServer(", "OnServerEvent", "RemoteEvent",
            "DataStore", "SetAsync(", "UpdateAsync(", "TakeDamage(",
            "Humanoid.Health=", "Rules.damageCastle(", "Rules.takeEggs(",
            "Rules.depositEggs(", "ProximityPrompt.Triggered"
        ):
            self.assertNotIn(forbidden, self.src)
        self.assertIn("if not RunService:IsStudio() then return end", self.src)
        self.assertEqual(self.src.count('Instance.new("ScreenGui")'), 1)
        self.assertEqual(self.src.count('Instance.new("BillboardGui")'), 1)

    def test_modes_real_world_names_and_no_ally_guidance(self):
        for required in (
            "EGGRUMBLE_QueuedMode", "BATTLE_ROYALE", 'mode~="TEAM"',
            "TacticalBattlefield", "Castle_", "EggVault",
            "OwnEggDeposit", "EGGRUMBLE_FieldItems", "NEUTRAL_BOSS_STONE_GIANT",
            "EGGRUMBLE_SelectedRole", "EGGRUMBLE_Eliminated",
            "if own==other then return false end",
            'if mode~="TEAM" then return false end',
            "return false end", "if closest then return closest",
        ):
            self.assertIn(required, self.src)

    def test_small_opt_in_mobile_and_keyboard_with_auto_hide(self):
        for required in (
            "INITIAL_SECONDS = 18", "UPDATE_SECONDS = 0.8",
            "toggle.Activated:Connect", "Enum.KeyCode.G",
            "bar.Visible=false", "toggle.Visible=false",
            "marker.Enabled=false", "marker.MaxDistance=380",
            "os.clock()-visibleSince>INITIAL_SECONDS",
            "if processed or not toggle.Visible then return end", "marker.Adornee=nil",
            "layoutForViewport()", "camera.ViewportSize.X",
            "math.min(294,math.max(90,width-132))",
        ):
            self.assertIn(required, self.src)
        self.assertEqual(len(re.findall(r"Heartbeat:Connect", self.src)), 1)
        self.assertNotIn("RenderStepped", self.src)
        self.assertNotIn("AlwaysOnTop=true", self.src)

    def test_manual_return_home_preserves_server_egg_authority(self):
        for token in (
            'returnHome.Name="ManualReturnHome"',
            'returnHome.Visible=expanded',
            'manuallyReturning=not manuallyReturning',
            'homeSelected:boolean',
            'if homeSelected then',
            'return home,"自城へ帰還（手動）"',
            'return nil,"自城へ帰還（手動）"',
            'Enum.KeyCode.H',
            'lastMode=mode;expanded=true;visibleSince=os.clock();manuallyReturning=false',
            'currentTarget=nil;lastMode="";manuallyReturning=false',
            'returnHome.Position=UDim2.fromOffset(left+barWidth+6,10)',
            'toggle.Position=UDim2.fromOffset(left+barWidth+60,10)',
        ):
            self.assertIn(token, self.src)
        self.assertLess(self.src.index("if homeSelected then"),
                        self.src.index("local item,itemDistance="))
        self.assertNotIn("EGGRUMBLE_CarriedEggs", self.src)
        self.assertNotIn("GetAttribute(\"heldEggs\")", self.src)

if __name__ == "__main__":
    unittest.main()
