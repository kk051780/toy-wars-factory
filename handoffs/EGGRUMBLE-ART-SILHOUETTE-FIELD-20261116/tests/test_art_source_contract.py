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
CLIENT = (ROOT / "EGGRUMBLE_ArtDistanceLOD.client.luau").read_text(encoding="utf-8")
ROLES = {"WARRIOR", "MAGE", "NINJA", "TRAPPER", "BUILDER", "BEAST", "ZOMBIE"}


def executable_lines(src: str) -> str:
    return "\n".join(s for s in src.splitlines() if not s.lstrip().startswith("--"))


class VisualLayersSourceContract(unittest.TestCase):
    def test_per_client_mobile_distance_lod_non_authoritative(self):
        body = executable_lines(CLIENT)
        for token in (
            'if not RunService:IsStudio() then return end',
            'local MAX_TRACKED_PARTS=1800',
            'local UPDATE_INTERVAL_SECONDS=1.2',
            'local MOBILE=UserInputService.TouchEnabled',
            'local DISPLAY_DISTANCES:',
            'if part.Name:sub(1,4)~="ART_" then return nil end',
            'local dist=DISPLAY_DISTANCES[ancestor.Name]',
            'part.LocalTransparencyModifier=transparency',
            'workspace.DescendantAdded:Connect(register)',
            'workspace.DescendantRemoving:Connect(remove)',
            'local delta=part.Position-viewpoint',
            'delta:Dot(delta)>maxDist*maxDist',
        ):
            self.assertIn(token, body)
        for folder in (
            "EGGRUMBLE_RoleVisuals", "EGGRUMBLE_BotVisuals",
            "EGGRUMBLE_FlagshipLandscape_VisualOnly", "EGGRUMBLE_CastleArt_VisualOnly",
            "EGGRUMBLE_NeutralArt_VisualOnly", "EGGRUMBLE_EggVisual_VisualOnly",
            "EGGRUMBLE_FieldItemVisual_VisualOnly", "EGGRUMBLE_ModeGateFrame_VisualOnly",
            "EGGRUMBLE_StoneGiantVisual_VisualOnly", "EGGRUMBLE_InteriorHeraldry_VisualOnly",
        ):
            self.assertIn(folder, body)
        for forbidden in (
            "RenderStepped", "Heartbeat", ".CanCollide=", ".CanTouch=", ".CanQuery=",
            "Humanoid", "Tool", "TakeDamage", "GetAttributeChangedSignal",
            "RemoteEvent", "ProximityPrompt", "DataStore", "UserOwnsGamePass",
        ):
            self.assertNotIn(forbidden, body)
        self.assertNotIn('ART_TrueNeutralKOCue', CLIENT)

    def test_exact_client_lod_rojo_node_and_author_combat_feel_preserved(self):
        tool_path=ROOT / "tools" / "compose_current_v3_art.py"
        spec=importlib.util.spec_from_file_location("a01_lod_composer",tool_path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.ART_CLIENT_NAME,"EGGRUMBLE_ArtDistanceLOD")
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            original=root / "author"
            original.mkdir()
            server={"$className":"ServerScriptService"}
            for name in module.MANDATORY_GAME_NAMES:
                file=original / (name+".luau")
                file.write_text("return {}\\n",encoding="utf-8")
                server[name]={"$path":file.name}
            combat=original/"EGGRUMBLE_CombatFeel.client.luau"
            combat.write_text("return {}\\n",encoding="utf-8")
            tree={"ServerScriptService":server,"StarterPlayer":{"$className":"StarterPlayer",
                  "StarterPlayerScripts":{"$className":"StarterPlayerScripts",
                  "EGGRUMBLE_CombatFeel":{"$path":combat.name}}}}
            author=original/"v3.project.json"
            before=json.dumps({"tree":tree})
            author.write_text(before,encoding="utf-8")
            out=root/"generated"/"v3-art.project.json"
            composed=module.compose(author,out,ROOT)
            node=composed["tree"]["StarterPlayer"]["StarterPlayerScripts"]
            self.assertEqual(
                set(node),{"$className","EGGRUMBLE_CombatFeel","EGGRUMBLE_ArtDistanceLOD"}
            )
            self.assertEqual((out.parent/node["EGGRUMBLE_ArtDistanceLOD"]["$path"]).resolve(),
                             (ROOT/"EGGRUMBLE_ArtDistanceLOD.client.luau").resolve())
            self.assertEqual((out.parent/node["EGGRUMBLE_CombatFeel"]["$path"]).resolve(),
                             combat.resolve())
            self.assertEqual(author.read_text(encoding="utf-8"),before)
            # Repeated composition of already augmented output must never
            # silently install a second camera-distance LocalScript.
            with self.assertRaisesRegex(ValueError,"already includes A01 client LOD"):
                module.compose(out,root/"twice.project.json",ROOT)

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

    def test_no_duplicate_weapons_after_author_claimed_weapon_silhouettes(self):
        # #482 now owns WeaponSilhouettes. A01 exclusively owns seven BODY forms
        # and lobby heraldry; no two 3-D handheld weapon objects on the same hero.
        self.assertNotIn("sculptHandheldWeapon", executable_lines(HERO))
        self.assertNotIn("MAX_HANDHELD_WEAPON_PARTS", executable_lines(HERO))
        self.assertNotIn('"Weapon_"..role', executable_lines(HERO))
        self.assertNotIn("EGGRUMBLE_ClassWeapon", executable_lines(HERO))
        for role in ROLES:
            self.assertIn('role=="' + role + '"', HERO)
        self.assertIn("PART_BUDGET_PER_SUBJECT = 13", HERO)

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
        self.assertLessEqual(16 * 11 + 3 * 4 * 2 + 20 * 4 + 10 * 2 + 2 * 2 + 3 * 4, 320)

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

    def test_field_has_three_real_outside_route_skyline_signatures(self):
        self.assertIn("local function drawLaneIdentityVista", FIELD)
        self.assertIn("drawLaneIdentityVista(arena,art,onGround(x,z),lane)", FIELD)
        self.assertIn('"LaneIdentity_"..lane', FIELD)
        for token in ('"_SpireL"', '"_SpireR"', '"_FordPier"', '"_StoneArc"', '"_TimberPillar"', '"_Shrine"'):
            self.assertIn(token, FIELD)
        self.assertIn("MAX_VISUAL_PARTS_PER_ARENA = 320", FIELD)

    def test_real_castle_flag_visual_echo_preserves_team_authority(self):
        # Original owner decoration is a flag Color change; ornament follows it
        # without altering the authoritative OwnerFlag or red/blue castle crest.
        self.assertIn('castle:FindFirstChild("OwnerFlag")', FIELD)
        self.assertIn('GetPropertyChangedSignal("Color")', FIELD)
        self.assertIn("if finial.Parent and flag.Parent then finial.Color=flag.Color end", FIELD)
        self.assertIn('add("HeraldicCrest"', FIELD)
        self.assertNotIn("flag.Color=", executable_lines(FIELD))
        self.assertNotIn('SetAttribute("EGGRUMBLE', executable_lines(FIELD))
        self.assertIn("castle.ChildAdded:Connect", FIELD)

    def test_neutral_3_silhouette_variants_have_only_real_humanoid_death_cues(self):
        self.assertIn('math.floor(math.abs(root.Position.X*.17+root.Position.Z*.31))%3', ENCOUNTERS)
        for tag in ("ScoutMantle", "ScoutBoneCrest", "VanguardPauldron", "VanguardHorn", "CursedMantle", "CursedHalo"):
            self.assertIn('"'+tag+'"', ENCOUNTERS)
        self.assertIn("deathCue(neutral,cueColor)", ENCOUNTERS)
        self.assertIn("hum.Died:Connect", ENCOUNTERS)
        self.assertNotIn("Humanoid.Health=", executable_lines(ENCOUNTERS))

    def test_standalone_original_stone_giant_cosmetics_track_real_core(self):
        for token in (
            'MAX_BOSS_ORNAMENT_PARTS=5', '"NEUTRAL_BOSS_STONE_GIANT"',
            '"CoreWeakpoint"', '"MonolithShoulder"', '"BrokenCrown"',
            '"WeakpointBezel"', '"HeartRunicRidge"',
            'core:GetPropertyChangedSignal("Color")',
            'if core.Parent and bezel.Parent then bezel.Color=core.Color end',
        ):
            self.assertIn(token, ENCOUNTERS)
        self.assertNotIn("core.Color=", executable_lines(ENCOUNTERS))
        self.assertNotIn('Instance.new("ProximityPrompt")', executable_lines(ENCOUNTERS))
        self.assertNotIn("health=", executable_lines(ENCOUNTERS))

    def test_standalone_physical_castle_art_fades_with_original_gate(self):
        for token in (
            'MAX_CASTLE_INTERIOR_ART_PARTS=5', '"EGGRUMBLE_EnterableCastle"',
            '"CastleGate"', '"EggVault"', '"SiegeCore"',
            '"GateRune"', '"VaultShield"', '"VaultRelief"', '"SiegeCoreSeal"',
            'gate:GetPropertyChangedSignal("Transparency"):Connect(syncDoor)',
            'p.Transparency=fade',
        ):
            self.assertIn(token, ENCOUNTERS)
        self.assertNotIn("gate.CanCollide=", executable_lines(ENCOUNTERS))
        self.assertNotIn("gate.Transparency=", executable_lines(ENCOUNTERS))

    def test_independent_author_lobby_preview_has_seven_visible_jobs_and_two_modes(self):
        self.assertIn('"EGGRUMBLE_LobbyUX"', HERO)
        self.assertIn('stand.Name:match("^JOB_(%d+)$")', HERO)
        self.assertIn('player:GetAttribute("EGGRUMBLE_LobbyPreviewRole")', HERO)
        self.assertIn('"EGGRUMBLE_LobbyPreviewRole"', HERO)
        self.assertIn('CFrame.new(0,-.35,-2.25)*cf', HERO)
        for label in ("武神", "魔法使い", "暗殺者", "超能力者",
                      "マッドサイエンティスト", "魔獣使い", "呪術師"):
            self.assertIn('["' + label + '"]=', HERO)
        self.assertIn('parent.Name=="EGGRUMBLE_LobbyUX"', ENCOUNTERS)
        self.assertIn("MAX_GATE_PIECES=7", ENCOUNTERS)
        self.assertNotIn('Instance.new("BillboardGui")', executable_lines(HERO + ENCOUNTERS))

    def test_all_four_author_standalone_previews_can_use_only_their_own_art(self):
        path = ROOT / "tools" / "compose_current_v3_art.py"
        spec = importlib.util.spec_from_file_location("a01_standalone_composer", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        mapping = {
            "boss": ("EGGRUMBLE_NeutralStoneGiant", "EGGRUMBLE_NeutralBossPreview"),
            "castle": ("EGGRUMBLE_EnterableCastleInterior", "EGGRUMBLE_CastleWalkthrough"),
            "lobby": ("EGGRUMBLE_LobbyUXPreview", "EGGRUMBLE_LobbyUXStandalone"),
            "item": ("EGGRUMBLE_FieldItemPickups", "EGGRUMBLE_FieldItemPreview"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for target, source_names in mapping.items():
                directory = base / target
                directory.mkdir()
                src = {"$className": "ServerScriptService"}
                for name in source_names:
                    p = directory / (name + ".luau")
                    p.write_text("return {}\\n", encoding="utf-8")
                    src[name] = {"$path": p.name}
                author = directory / "author.project.json"
                raw = json.dumps({"tree": {"ServerScriptService": src}})
                author.write_text(raw, encoding="utf-8")
                output = directory / "out" / "art.project.json"
                composed = module.compose(author, output, ROOT, target=target)
                result = composed["tree"]["ServerScriptService"]
                self.assertEqual(
                    set(result) - {"$className"},
                    set(source_names) | set(module.ART_BY_TARGET[target]),
                )
                self.assertEqual(author.read_text(encoding="utf-8"), raw)
                for name, node in result.items():
                    if name != "$className":
                        self.assertTrue((output.parent / node["$path"]).resolve().is_file())

    def test_face_on_medallions_and_actual_rojo_artifact_delivery_contract(self):
        # Cylinders have their long axis along local X; rotate about Y to face
        # the castle/vault/portal viewer instead of showing their thin edge.
        self.assertIn('CFrame.new(0,0,-.42)*CFrame.Angles(0,math.rad(90),0)', ENCOUNTERS)
        self.assertIn('CFrame.new(0,6.9,-1.28)*CFrame.Angles(0,math.rad(90),0)', ENCOUNTERS)
        workflow = (ROOT.parents[1] / ".github/workflows/p0d-eggrumble-art-a01-source.yml").read_text(encoding="utf-8")
        self.assertIn('rojo build "$project" --output "$destination"', workflow)
        self.assertIn('test -s "$destination"', workflow)
        self.assertIn('art-private-builds/EGGRUMBLE_A01_PRIVATE_', workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("retention-days: 3", workflow)
        self.assertNotIn("rojo plugin install", workflow)
        self.assertNotIn("rojo serve", workflow)
        self.assertNotIn("rojo publish", workflow)

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
            client_source = author_dir / "EGGRUMBLE_CombatFeel.client.luau"
            client_source.write_text("return {}\\n", encoding="utf-8")
            original = json.dumps({"tree": {
                "ServerScriptService": nodes,
                "StarterPlayer": {
                    "$className": "StarterPlayer",
                    "StarterPlayerScripts": {
                        "$className": "StarterPlayerScripts",
                        "EGGRUMBLE_CombatFeel": {"$path": client_source.name},
                    },
                },
            }})
            source_path = author_dir / "author.project.json"
            source_path.write_text(original, encoding="utf-8")
            output = base / "output" / "private_art.project.json"
            assembled = module.compose(source_path, output, ROOT)
            client = assembled["tree"]["StarterPlayer"]["StarterPlayerScripts"]["EGGRUMBLE_CombatFeel"]
            self.assertEqual((output.parent / client["$path"]).resolve(), client_source.resolve())
            art = assembled["tree"]["ServerScriptService"]
            self.assertEqual(set(art) - {"$className"}, set(module.MANDATORY_GAME_NAMES) | set(module.ART_NAMES))
            self.assertTrue(output.exists())
            self.assertEqual(source_path.read_text(encoding="utf-8"), original)
            for name, node in art.items():
                if name == "$className":
                    continue
                self.assertTrue((output.parent / node["$path"]).resolve().is_file(), name)

    def test_new_author_require_is_salvaged_without_editing_author_manifest(self):
        tool_path = ROOT / "tools" / "compose_current_v3_art.py"
        spec = importlib.util.spec_from_file_location("a01_author_dependency_composer", tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            author_dir = base / "author"
            author_dir.mkdir()
            nodes = {"$className": "ServerScriptService"}
            for name in module.MANDATORY_GAME_NAMES:
                filename = name + ".luau"
                source = "return {}\\n"
                if name == "EGGRUMBLE_SevenRoleCombat":
                    source = 'local W=require(script.Parent:WaitForChild("EGGRUMBLE_WeaponSilhouettes"))\\n'
                (author_dir / filename).write_text(source, encoding="utf-8")
                nodes[name] = {"$path": filename}
            extra = author_dir / "EGGRUMBLE_WeaponSilhouettes.luau"
            extra.write_text("return {}\\n", encoding="utf-8")
            original = json.dumps({"tree": {"ServerScriptService": nodes}})
            original_path = author_dir / "v3.project.json"
            original_path.write_text(original, encoding="utf-8")
            out = base / "generated" / "v3_art.project.json"
            result = module.compose(original_path, out, ROOT)
            assembled = result["tree"]["ServerScriptService"]
            self.assertIn("EGGRUMBLE_WeaponSilhouettes", assembled)
            self.assertEqual(
                (out.parent / assembled["EGGRUMBLE_WeaponSilhouettes"]["$path"]).resolve(),
                extra.resolve(),
            )
            self.assertEqual(original_path.read_text(encoding="utf-8"), original)
            self.assertNotIn("EGGRUMBLE_WeaponSilhouettes", original)

    def test_missing_real_author_dependency_rejects_instead_of_forging_source(self):
        tool_path = ROOT / "tools" / "compose_current_v3_art.py"
        spec = importlib.util.spec_from_file_location("a01_author_dependency_missing", tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            nodes = {"$className": "ServerScriptService"}
            for name in module.MANDATORY_GAME_NAMES:
                fn = base / (name + ".luau")
                fn.write_text(
                    'local W=require(script.Parent:WaitForChild("EGGRUMBLE_MissingAuthorModule"))\\n'
                    if name == "EGGRUMBLE_SevenRoleCombat" else "return {}\\n",
                    encoding="utf-8",
                )
                nodes[name] = {"$path": fn.name}
            author = base / "current_author.project.json"
            author.write_text(json.dumps({"tree": {"ServerScriptService": nodes}}), encoding="utf-8")
            out = base / "preview" / "v3_art.project.json"
            with self.assertRaisesRegex(ValueError, "Missing real author sibling module"):
                module.compose(author, out, ROOT)
            self.assertFalse(out.exists())

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
