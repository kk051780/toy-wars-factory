"""Source-only regression for additive EGGRUMBLE studio art.

Run: python3 -m unittest discover -s handoffs/EGGRUMBLE-ART-SILHOUETTE-FIELD-20261116/tests
This is NOT a Luau compiler, real Studio device, or art/FUN approval.
"""
from pathlib import Path
import re
import json
import unittest
import importlib.util
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HERO = (ROOT / "EGGRUMBLE_HeroSilhouetteArt.server.luau").read_text(encoding="utf-8")
FIELD = (ROOT / "EGGRUMBLE_FlagshipFieldArt.server.luau").read_text(encoding="utf-8")
ENCOUNTERS = (ROOT / "EGGRUMBLE_EncounterReadabilityArt.server.luau").read_text(encoding="utf-8")
ROLES = {"WARRIOR", "MAGE", "NINJA", "TRAPPER", "BUILDER", "BEAST", "ZOMBIE"}


def executable_lines(src: str) -> str:
    return "\n".join(s for s in src.splitlines() if not s.lstrip().startswith("--"))


class VisualLayersSourceContract(unittest.TestCase):
    def test_studio_private_only(self):
        for src in (HERO, FIELD, ENCOUNTERS):
            self.assertIn('game:GetService("RunService")', src)
            self.assertIn("if not RunService:IsStudio() then return end", src)

    def test_all_seven_distinct_role_silhouettes(self):
        self.assertEqual(set(re.findall(r'role=="([A-Z]+)"', HERO)), ROLES)
        for role in ROLES:
            self.assertIn(role + "={base=Color3.fromRGB(", HERO)
        self.assertIn("GetAttributeChangedSignal", HERO)
        self.assertIn('"P0DPreviewRole"', HERO)

    def test_v3_real_class_state_and_seven_lobby_minis(self):
        # Latest V3 gameplay equips EGGRUMBLE_Role, preview only P0DPreviewRole.
        self.assertIn('player:GetAttribute("EGGRUMBLE_Role")', HERO)
        self.assertIn('player:GetAttribute("EGGRUMBLE_SelectedRole")', HERO)
        self.assertIn('player:GetAttribute("P0DPreviewRole")', HERO)
        for role in ROLES:
            self.assertIn('role=="' + role + '"', HERO)
        self.assertIn('stand.Name:match("^ROLE_([A-Z]+)$")', HERO)
        self.assertIn("EGGRUMBLE_LobbyRoleMiniatures_VisualOnly", HERO)
        self.assertIn("MAX_LOBBY_ROLE_STAND_PARTS = 4", HERO)
        self.assertIn("standParts>=MAX_LOBBY_ROLE_STAND_PARTS", HERO)
        self.assertIn("player.CharacterAdded:Connect(onCharacterAdded)", HERO)
        self.assertIn("task.delay(.35", HERO)

    def test_real_author_item_art_is_capped_and_no_pickup_side_effect(self):
        for snippet in (
            'item.Name:match("^ITEM_%d+_(%u+)$")',
            'MAX_DECORATED_ITEMS_PER_WORLD=12',
            'activeItems[world]=(activeItems[world] or 0)+1',
            '"EGGRUMBLE_ItemPreviewWorld"',
            '"EGGRUMBLE_FieldItemVisual_VisualOnly"',
            'item.Destroying:Connect',
            'kind=="HEAL"', 'kind=="DASH"',
        ):
            self.assertIn(snippet, ENCOUNTERS)
        for forbidden in ("prompt.Triggered", "Humanoid.WalkSpeed=", "ForceField", "ProximityPrompt.new"):
            self.assertNotIn(forbidden, executable_lines(ENCOUNTERS))

    def test_no_dynamic_gameplay_authority(self):
        forbidden = (
            "DataStoreService", "RemoteEvent", "RemoteFunction", "TeleportService",
            "TakeDamage(", "LoadAnimation(", "DamageCastle(", "depositEggs(",
            "takeEggs(", "Coins", "Robux", "ProcessReceipt", "Humanoid.Health=",
            "Terrain:Fill", "Terrain:Clear", ".CanCollide=true",
        )
        for src in (executable_lines(HERO), executable_lines(FIELD), executable_lines(ENCOUNTERS)):
            for token in forbidden:
                self.assertNotIn(token, src, f"new art may not own {token}")

    def test_art_parts_cannot_block_paths(self):
        for src in (HERO, FIELD, ENCOUNTERS):
            for token in ("p.CanCollide=false", "p.CanTouch=false", "p.CanQuery=false", "p.CastShadow=false"):
                self.assertIn(token, src)
        self.assertNotIn("Touched:Connect", HERO + FIELD + ENCOUNTERS)
        self.assertNotIn("BillboardGui", executable_lines(HERO + FIELD + ENCOUNTERS))

    def test_fixed_low_mobile_budgets(self):
        self.assertIn("PART_BUDGET_PER_SUBJECT = 13", HERO)
        self.assertIn("made>=PART_BUDGET_PER_SUBJECT", HERO)
        self.assertIn("MAX_VISUAL_PARTS_PER_ARENA = 320", FIELD)
        self.assertIn("MAX_CASTLE_PARTS = 11", FIELD)
        self.assertIn("used>=MAX_CASTLE_PARTS", FIELD)
        self.assertIn("(budgets[arena] or 0)>=MAX_VISUAL_PARTS_PER_ARENA", FIELD)
        self.assertLessEqual(16 * 11 + 3 * 4 * 2 + 20 * 4 + 10 * 2 + 2 * 2, 320)

    def test_only_existing_v3_arena_decorated(self):
        for token in ("TEAM_Arena", "BATTLE_ROYALE_Arena", "TacticalBattlefield", "StandardCore"):
            self.assertIn(token, FIELD)
        self.assertIn("EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW", FIELD)
        self.assertIn("EGGRUMBLE_CastleArt_VisualOnly", FIELD)
        self.assertNotIn('Instance.new("SpawnLocation")', FIELD)
        self.assertNotIn('Instance.new("Terrain")', FIELD)

    def test_rojo_previews_pin_only_existing_author_sources(self):
        projects = {
            "EGGRUMBLE_V3_ART_STUDIO.project.json": 8,
            "EGGRUMBLE_SEVEN_HERO_ART_STUDIO.project.json": 2,
        }
        for filename, expected in projects.items():
            project = json.loads((ROOT / filename).read_text(encoding="utf-8"))
            nodes = project["tree"]["ServerScriptService"]
            self.assertEqual(len(nodes) - 1, expected)  # one $className entry
            for name, spec in nodes.items():
                if name == "$className":
                    continue
                resolved = (ROOT / spec["$path"]).resolve()
                self.assertTrue(resolved.is_file(), f"broken Rojo source: {filename}:{name}")

    def test_neutral_battle_cues_use_real_death_and_are_capped(self):
        for needle in (
            'neutral.Name~="HordeSoldier"',
            'neutral:GetAttribute("EGGRUMBLE_Neutral")~=true',
            "hum.Died:Connect",
            "if fired then return end",
            "MAX_SIMULTANEOUS_KO_BURSTS=8",
            "MAX_DECORATED_NEUTRALS_PER_ARENA=24",
            "activeBurst>=MAX_SIMULTANEOUS_KO_BURSTS",
            "neutral.Destroying:Connect",
            "activeNeutrals[arena]=",
        ):
            self.assertIn(needle, ENCOUNTERS)
        for token in ("Heartbeat:Connect", 'SetAttribute("EGGRUMBLE_NeutralKOs"', "LastAttackerId", "TakeDamage("):
            self.assertNotIn(token, executable_lines(ENCOUNTERS))

    def test_loot_and_lobby_are_readable_but_not_authoritative(self):
        for needle in (
            "MAX_DECORATED_EGGS_PER_ARENA=28",
            "FieldEgg_", "ReleasedEgg_", "OwnEggDeposit", "EggVault",
            "TEAM_PORTAL", "BATTLE_ROYALE_PORTAL", "DEFENSE_",
            "MAX_GATE_PIECES=7", "EGGRUMBLE_EggVisual_VisualOnly",
            "egg.Destroying:Connect", "EGGRUMBLE_ModeGateFrame_VisualOnly",
        ):
            self.assertIn(needle, ENCOUNTERS)
        for token in ('Instance.new("ProximityPrompt")', "SetAttribute(", "getPlayerData("):
            self.assertNotIn(token, executable_lines(ENCOUNTERS))

    def test_art_instance_budget_under_500_per_arena(self):
        # Field cap + 24*2 neutral + 28*2 egg + 12*2 pickups + 16 castles*2 stations
        # + 2 lobby gates*6 + 5 defense stands = 497 conservative visual cap.
        self.assertLessEqual(320 + 24 * 2 + 28 * 2 + 12 * 2 + 16 * 2 + 2 * 6 + 5, 500)

    def test_moving_bot_armor_is_welded_and_not_frozen(self):
        self.assertIn("piece(parent,torso,name,shape,size,offset,color,Enum.Material.Metal,false)", HERO)
        self.assertIn("weld.Part0=anchor", HERO)
        self.assertIn("weld.Part1=p", HERO)

    def test_dynamic_latest_author_studio_manifest_is_non_mutating(self):
        tool_path = ROOT / "tools" / "compose_current_v3_art.py"
        self.assertTrue(tool_path.exists())
        spec = importlib.util.spec_from_file_location("a01_composer", tool_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            author_dir = base / "author"
            author_dir.mkdir()
            nodes = {"$className": "ServerScriptService"}
            for name in module.MANDATORY_GAME_NAMES:
                suffix = ".server.luau" if name.endswith("Preview") else ".luau"
                filename = name + suffix
                source = 'return {}\\n'
                if name == "EGGRUMBLE_LobbyCastleModesPreview":
                    source = 'local G=require(script.Parent:WaitForChild("EGGRUMBLE_InteractionGuard"))\\n'
                (author_dir / filename).write_text(source, encoding="utf-8")
                nodes[name] = {"$path": filename}
            original = json.dumps({"tree": {"ServerScriptService": nodes}})
            source_path = author_dir / "author.project.json"
            source_path.write_text(original, encoding="utf-8")
            output = base / "output" / "private_art.project.json"
            assembled = module.compose(source_path, output, ROOT)
            art = assembled["tree"]["ServerScriptService"]
            self.assertEqual(set(art) - {"$className"}, set(module.MANDATORY_GAME_NAMES) | set(module.ART_NAMES))
            self.assertTrue(output.exists())
            self.assertEqual(source_path.read_text(encoding="utf-8"), original)
            for name, node in art.items():
                if name == "$className":
                    continue
                self.assertTrue((output.parent / node["$path"]).resolve().is_file(), name)

    def test_dynamic_composer_rejects_outdated_author_module_set(self):
        tool_path = ROOT / "tools" / "compose_current_v3_art.py"
        spec = importlib.util.spec_from_file_location("a01_composer_negative", tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            author = base / "stale.project.json"
            author.write_text(json.dumps({"tree": {"ServerScriptService": {
                "$className": "ServerScriptService",
                "EGGRUMBLE_LobbyCastleModesPreview": {"$path": "missing.server.luau"}
            }}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing latest author V3 module"):
                module.compose(author, base / "composed.project.json", ROOT)
            self.assertFalse((base / "composed.project.json").exists())

    def test_reversible_visual_only_namespaces(self):
        self.assertIn('"EGGRUMBLE_RoleVisuals"', HERO)
        self.assertIn('"EGGRUMBLE_BotVisuals"', HERO)
        self.assertIn('"EGGRUMBLE_FlagshipLandscape_VisualOnly"', FIELD)
        self.assertIn('existing:Destroy()', HERO)
        self.assertNotIn('script.Parent:WaitForChild("Game")', HERO + FIELD)


if __name__ == "__main__":
    unittest.main()
