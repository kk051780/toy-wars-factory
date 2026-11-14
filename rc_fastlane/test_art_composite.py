"""The complete eight-feature preview must never mutate canonical RC66."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from rc_fastlane import build_art_composite as art


class EightFeatureCandidateSafety(unittest.TestCase):
    def test_all_eight_real_source_blobs(self):
        self.assertEqual(len(art.pinned_art()),8)

    def test_composite_includes_no_server_game_replacement(self):
        a=art.pinned_art()
        self.assertEqual(set(a),{
            "server/CastleBattlefield.server.luau",
            "server/CastleDetailArt.server.luau",
            "server/FantasyWorldArt.server.luau",
            "server/H1CoastalSeascape.server.luau",
            "server/H1SeaGroundRepair.server.luau",
            "server/ArtMinionSilhouette.server.luau",
            "client/FB015CharacterArt.client.luau",
            "client/BattleHUDGovernor.client.luau",
        })
        self.assertNotIn("server/Game.server.luau",a)
        self.assertNotIn("server/GoroganRigDriver.luau",a)

    def test_numeric_hp_minimal_hud_and_world_label_contract(self):
        code=art.pinned_art()["client/BattleHUDGovernor.client.luau"].decode("utf8")
        for token in ("BattleSelfHPNumerical", "HP %d/%d", "TrapRaidersS1Remote",
                      "TrapRaidersS1HUD", "P0D_HUD_CLEAN_GOVERNOR",
                      "maxHp", 'phase == "ACTIVE"', "MaxDistance = 36",
                      "instructionLabel.Visible = false", "updateOptionalAll()"):
            self.assertIn(token,code)
        self.assertNotIn("FireServer(",code)
        self.assertNotIn("DataStoreService",code)

    def test_castle_detail_layer_has_correct_anchor_and_no_game_collision(self):
        s=art.pinned_art()["server/CastleDetailArt.server.luau"].decode("utf8")
        self.assertIn('if not RunService:IsStudio() then return end',s)
        self.assertIn('OWNER361_CASTLE_WORLD_V1',s)
        self.assertIn('GATE_TOWER_-1',s)
        self.assertIn('GRAND_KEEP',s)
        self.assertIn('PORTCULLIS_ARCH_TOP',s)
        self.assertIn('KEEP_HERALDRY',s)
        self.assertIn('BRAZIER_',s)
        self.assertIn('MAX_PARTS = 190',s)
        self.assertIn('p.CanCollide = false',s)
        self.assertIn('p.CanQuery = false',s)
        self.assertNotIn('Instance.new("RemoteEvent")',s)
        self.assertNotIn('TakeDamage(',s)

    def test_castle_authored_trees_are_on_dry_north_shore(self):
        castle=art.pinned_art()["server/CastleBattlefield.server.luau"].decode("utf8")
        self.assertIn('local pz = -94 - math.floor((j - 1) / 3) * 35',castle)
        self.assertNotIn('local pz = -80',castle)
        # The near row is z=-94 and its 15-stud foliage crown reaches to
        # z=-86.5, beyond the coastal channel edge at z=-83.
        self.assertLess(-94 + 15 / 2, -83)
        self.assertGreater(-94 - 35 - 15 / 2, -147)

    def test_forest_waits_for_expanded_castle_before_scattering(self):
        code=art.pinned_art()["server/FantasyWorldArt.server.luau"].decode("utf8")
        gates=("OWNER361_CASTLE_WORLD_V1", "red:FindFirstChild",
               "blue:FindFirstChild", "ground.Size.Z - 294",
               "FB015_FOREST_CASTLE_GEOMETRY_NOT_READY_FAIL_CLOSED")
        for marker in gates:
            self.assertIn(marker,code)
        self.assertLess(code.index("OWNER361_CASTLE_WORLD_V1"),
                        code.index("local sideZ="))
        self.assertIn('folder:SetAttribute("ForestPlacedAfterCastleExpanded",true)',code)
        self.assertIn('folder:SetAttribute("ForestSourceMapDepth",ground.Size.Z)',code)
        self.assertIn('task.wait(.1)',code)

    def test_minion_cloak_sways_without_physics_or_game_authority(self):
        code=art.pinned_art()["server/ArtMinionSilhouette.server.luau"].decode("utf8")
        # Real original MusouHorde uses Model:PivotTo. Decorative parts
        # remain anchored inside that Model, and only the selected cape/fur
        # gets animated relative to the current authoritative Core pose.
        self.assertIn('item.Anchored = true',code)
        self.assertIn('item.CanCollide = false',code)
        self.assertIn('item.CanTouch = false',code)
        self.assertIn('item.CanQuery = false',code)
        self.assertIn('movingRelative=core.CFrame:ToObjectSpace(moving.CFrame)',code)
        self.assertIn('item.moving.CFrame = item.core.CFrame * item.movingRelative',code)
        self.assertIn('CFrame.Angles(sway*.10+ko*.22,flutter*.055,',code)
        self.assertIn('sway*.085+recoil*.23+ko*.28)',code)
        self.assertIn('CFrame.new(0,-.12*ko,.18*recoil)',code)
        self.assertIn('P0D_ART_MINION_SWAY_VISUAL',code)
        self.assertNotIn('WeldConstraint',code)
        self.assertNotIn('item.Anchored = false',code)
        self.assertNotIn('item.core.CFrame =',code)
        self.assertNotIn('TakeDamage(',code)
        self.assertNotIn('FireServer(',code)

    def test_server_hit_slash_and_ko_are_reused_visual_only(self):
        code=art.pinned_art()["server/ArtMinionSilhouette.server.luau"].decode("utf8")
        # 8 normal + 1 elite: exactly two persistent beams for each NPC,
        # triggered by original server-owned hit flash and KO text.
        for token in (
            'makeSlashArcs(core,accent,isElite)', 'Instance.new("Beam")',
            'beam.Name = "ART_SERVER_HIT_SLASH_"', 'beam.Enabled = false',
            'beam.FaceCamera = true', 'NumberSequenceKeypoint.new(1,1)',
            'if flashing and not item.lastHit then',
            'item.slashStart = now', 'arc.Enabled = true',
            'if dead then', 'item.sparks:Emit(22)',
            'local remain = 1 - (os.clock()-item.slashStart)/.36',
            'arc.Enabled = false', 'arc.Width0 = item.slashWidth * remain',
            'item.CanCollide = false', 'item.CanQuery = false',
        ):
            self.assertIn(token,code)
        self.assertEqual(code.count('Instance.new("Beam")'),1)
        self.assertNotIn('Instance.new("RemoteEvent")',code)
        self.assertNotIn('FireServer(',code)
        self.assertNotIn('TakeDamage(',code)
        self.assertNotIn('item.core.CFrame =',code)

    def test_direct_damage_cue_for_fast_hit_and_ko_without_authority(self):
        code=art.pinned_art()["server/ArtMinionSilhouette.server.luau"].decode("utf8")
        for marker in (
            'core:GetPropertyChangedSignal("Color")',
            'cueText:GetPropertyChangedSignal("Text")',
            'originalHPText(value)', 'isOriginalGold(core.Color)',
            'if now-item.lastImpactAt < .06 then return end',
            'item.streak = if previousGap < 1.25 then',
            'fireHitVisual(entry)', 'fireKOCosmetic(entry)',
            'local recoil=math.clamp((item.recoilUntil-now)/.19,0,1)',
            'local ko=math.clamp((item.koUntil-now)/.62,0,1)',
            'clearVisualSignals(item)',
            'connection:Disconnect()',
            'table.clear(item.connections)',
            'item.lastDeath = false',
        ):
            self.assertIn(marker,code)
        self.assertEqual(code.count('Instance.new("Beam")'),1)
        self.assertNotIn('Instance.new("RemoteEvent")',code)
        self.assertNotIn('TakeDamage(',code)
        self.assertNotIn('FireServer(',code)
        self.assertNotIn('item.core.CFrame =',code)

    def test_minion_and_gorogan_cosmetics_have_distinct_owners(self):
        a=art.pinned_art()
        self.assertNotIn(b"MUSOU_MINION_",a["client/FB015CharacterArt.client.luau"])
        self.assertNotIn(b"Gorogan_ServerRig",a["server/ArtMinionSilhouette.server.luau"])

    def test_gorogan_client_art_waits_for_replicated_rig_bounded(self):
        source=art.pinned_art()["client/FB015CharacterArt.client.luau"].decode("utf8")
        self.assertIn('MAX_REPLICATION_WAIT_STEPS = 40',source)
        self.assertIn('REPLICATION_WAIT_SECONDS = .15',source)
        self.assertIn('pending[model] = true',source)
        self.assertIn('pending[model] = nil',source)
        self.assertIn('task.spawn(function()',source)
        self.assertIn('FB015_BeastArtClientAttached',source)
        self.assertIn('FB015_GOROGAN_ART_REPLICATION_WAIT_EXPIRED',source)
        self.assertIn('local added = Workspace.DescendantAdded:Connect',source)
        self.assertIn('added:Disconnect()',source)
        self.assertNotIn('MUSOU_MINION_',source)
        self.assertNotIn('humanoid.Health =',source)
        self.assertNotIn('FireServer(',source)

    def test_coastal_solid_floor_is_carved_into_real_water_and_dry_paths(self):
        scripts=art.pinned_art()
        code=scripts["server/H1SeaGroundRepair.server.luau"].decode("utf8")
        self.assertIn('if not RunService:IsStudio() then return end',code)
        self.assertIn('sea:GetAttribute("WaterTerrainCreated")==true',code)
        self.assertIn('math.abs(grass.Size.X-370)',code)
        self.assertIn('dryLand("NORTH_HIGHLANDS"',code)
        self.assertIn('dryLand("SOUTH_MAINLAND"',code)
        self.assertIn('dryLand("WEST_COAST_FLANK"',code)
        self.assertIn('dryLand("EAST_COAST_FLANK"',code)
        self.assertIn('grass.Transparency = 1',code)
        self.assertIn('grass.CanCollide = false',code)
        self.assertIn('terrain:FillBlock(',code)
        self.assertIn('Vector3.new(246,7,52)',code)
        self.assertIn('Vector3.new(side*85,-2.95,-53)',code)
        self.assertIn('SeaRouteVisualOnly',scripts["server/H1CoastalSeascape.server.luau"].decode("utf8"))
        self.assertNotIn('Instance.new("RemoteEvent")',code)

    def test_reject_missing_source_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist=Path(tmp)/"none"
            candidate=Path(tmp)/"scratch"
            with self.assertRaises(AssertionError):
                art.compose(dist,candidate)
            self.assertFalse(candidate.exists())

    def test_compiler_metadata_has_exact_counts_and_flags(self):
        import inspect
        body=inspect.getsource(art.compose)
        self.assertIn('locks["total_scripts"]=74',body)
        self.assertIn('features["total_sources"]=74',body)
        self.assertIn('assert len(after) == 74',body)
        self.assertIn('LOCK_TOTAL_MUST_MATCH_REAL_SCRIPT_COUNT',body)

    def test_all_sources_have_valid_sha_pins(self):
        for category,pin,path,name,flag in art.SPECS:
            self.assertEqual(art.gitblob((art.ART/name).read_bytes()),pin)


if __name__=="__main__":
    unittest.main()
