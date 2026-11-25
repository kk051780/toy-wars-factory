#!/usr/bin/env python3
"""Regression tests for a real but optional 32nd V3 Studio traversal source."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

DIR = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("lss_compose", DIR / "compose_optional32.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SOURCE = (DIR / "EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text(encoding="utf-8")


class LandSeaSkySourceTests(unittest.TestCase):
    def test_studio_only_and_canonical_authority(self):
        self.assertIn("if not RunService:IsStudio() then return end", SOURCE)
        for forbidden in ["Instance.new(\"RemoteEvent\")", "DataStoreService",
                          "NeutralHorde=Instance", "Instance.new(\"BindableEvent\")",
                          "LastAttackerId", "TakeDamage(", "SetAttribute(\"EGGRUMBLE_Combo\""]:
            self.assertNotIn(forbidden, SOURCE)

    def test_roles_and_terrain_and_seat_controls(self):
        for value in ["BUILDER", "BEAST", "TRAPPER", "TEAM_Arena",
                      "BATTLE_ROYALE_Arena", "COASTAL_WATER_VISUAL_ONLY",
                      "SkyIsland_", "PublicCloudLift_", "PublicSeaDock",
                      "SEA_BOAT", "AIRSHIP", "SEA_BEAST", "SKY_BEAST",
                      "VehicleSeat", "ThrottleFloat", "SteerFloat",
                      "Workspace:Blockcast", "NeutralHordeCoastBeacon",
                      "FlyAscendControl", "FlyDescendControl",
                      "FlightTargetAltitude", "FLIGHT_VERTICAL_SPEED"]:
            with self.subTest(value=value):
                self.assertIn(value, SOURCE)

    def test_authorized_variable_altitude_flight(self):
        # Only the actual seated owner may change altitude, independently
        # of client-controlled throttle/steering, and travel is server-clamped.
        for marker in [
            'requester~=player', 'seat.Occupant~=h',
            'data.targetY=math.clamp(data.targetY+ctrl.sign*FLIGHT_STEP',
            'v.targetY-cf.Position.Y,-FLIGHT_VERTICAL_SPEED*step',
            'y+FLIGHT_MIN_Y_ABOVE_GROUND,y+FLIGHT_MAX_Y_ABOVE_GROUND',
            'Workspace:Blockcast', 'v.targetY=cf.Position.Y',
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, SOURCE)
        self.assertNotIn('v.flying and cloudY+8 or y+5', SOURCE)

    def test_offshore_sea_route_and_safe_return(self):
        # Geometry/authorship assertions are source-only, NOT engine validation.
        for marker in [
            "OFFSHORE_NAVIGABLE_SEA_LANE",
            "SEA_OUTER_LENGTH = 260",
            "SEA_ROUTE_HALF_WIDTH = 275",
            "offshoreEndZ=z+halfZ+SEA_OUTER_LENGTH",
            "OffshoreSafeDock_",
            "PublicOffshoreShuttle",
            "offshorePads[side]",
            "publicTravel(p,landDock.Position",
            "v.lastPilot=hum",
            "not hum and v.lastPilot",
            "local dismountOnDock=false",
            "math.abs(root.Position.X-dock.Position.X)<=dock.Size.X/2-2",
            "math.abs(root.Position.Z-dock.Position.Z)<=dock.Size.Z/2-2",
            "and not dismountOnDock",
            "craft:GetPivot().Position.Z>z+halfZ+10",
            "offshoreEndZ-SEA_OUTER_MARGIN",
            "local exclude=vehicleSweepExclusions(",
            "craft,water,offshoreWater,hum.Parent)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, SOURCE)
        self.assertIn('world:FindFirstChild("Castle_"..tostring(player.UserId))', SOURCE)
        self.assertIn('world.Parent:FindFirstChild(world.Name)==world', SOURCE)
        self.assertNotIn('FillBlock(', SOURCE)
        self.assertNotIn('FillRegion(', SOURCE)

    def test_public_pacing_and_unrestricted_rescue(self):
        self.assertIn("PUBLIC_TRAVEL_COOLDOWN = 2.5", SOURCE)
        self.assertIn("GQ8_LSS_PUBLIC_TRAVEL_PACING_20261118_BEGIN", SOURCE)
        self.assertIn("if prev and now-prev<PUBLIC_TRAVEL_COOLDOWN then return false end", SOURCE)
        self.assertIn("if not safeMove(player,at,mode,world) then return false end", SOURCE)
        self.assertIn("publicTravelAt[player.UserId]=now", SOURCE)
        for marker in [
            "publicTravel(p,offshorePads[-1].Position",
            "publicTravel(p,landDock.Position",
            "publicTravel(p,Vector3.new(sx,cloudY+5,skyZ))",
            "publicTravel(p,groundLift.Position",
            "safeMove(v.owner,landDock.Position",
            "table.clear(publicTravelAt)",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, SOURCE)

    def test_real_horde_musou_feedback_no_second_kill_writer(self):
        # Source policy: read-only confirmed Swarm neutral-KOs; no fake soldiers.
        for marker in [
            "RealHordeFrontlineCounter",
            'world:FindFirstChild("NeutralHorde")',
            'model:GetAttribute("EGGRUMBLE_Neutral")==true',
            "h and h.Health>0",
            'player:GetAttributeChangedSignal("EGGRUMBLE_Combo")',
            'player:GetAttribute("EGGRUMBLE_NeutralKOs")',
            'player:GetAttribute("EGGRUMBLE_Combo")',
            "musouConfirmedMilestone(ko,combo,lastKOAdvanceAt[userId]",
            'player:GetAttributeChangedSignal("EGGRUMBLE_NeutralKOs")',
            'player:GetAttributeChangedSignal("EGGRUMBLE_Combo")',
            "lastKOAdvanceAt[userId]=now",
            "lastComboAdvanceAt[userId]=now",
            "lastShownCombo[userId]=combo",
            "if ko<oldKO or combo<oldCombo then",
            "MUSOU_ATTRIBUTE_SYNC_SECONDS = 0.75",
            'not matchHuman(player,mode,world,nil)',
            "MUSOU_MAX_BURSTS_PER_SEC = 2",
            "MUSOU_EFFECT_TTL = 0.46",
            "EGGRUMBLE_REAL_KO_MUSOU_WAVE",
            "Debris:AddItem(wave,MUSOU_EFFECT_TTL)",
            "for player in pairs(combatConnections) do unwatchCombo(player) end",
            "for _,conn in ipairs(pair) do conn:Disconnect() end",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, SOURCE)
        self.assertNotIn("Instance.new(\"Humanoid\")", SOURCE)
        self.assertNotIn('SetAttribute("EGGRUMBLE_NeutralKOs"', SOURCE)
        self.assertNotIn('SetAttribute("EGGRUMBLE_Combo"', SOURCE)
        self.assertNotIn('for _,conn in pairs(combatConnections)', SOURCE)

    def test_tide_trap_current_living_character_and_successful_move(self):
        # Existing one-shot protection stays intact. A stale/dead avatar
        # cannot spend the trap; failed server move must reset the claim.
        trap = SOURCE.split("t.Touched:Connect(function(other)", 1)[1].split(
            "Debris:AddItem(t,TRAP_LIFETIME)", 1)[0]
        checks = [
            "if fired or not active or not t.Parent then return end",
            "if guest.Character~=ch then return end",
            'local hum=ch:FindFirstChildOfClass("Humanoid")',
            "hum.Health<=0", "fired=true",
            "if not safeMove(guest,seaRaft.Position", "fired=false",
            "t:Destroy()",
        ]
        owner_gate, victim_gate = trap.split(
            '    local ch=other:FindFirstAncestorOfClass("Model")', 1)
        # A caster-invalid trap now has its own early Destroy(); isolate the
        # *victim success* Destroy() so both guards remain independently strict.
        self.assertIn('matchHuman(owner,mode,world,"TRAPPER")', owner_gate)
        self.assertEqual(owner_gate.count("t:Destroy()"), 1)
        self.assertEqual(victim_gate.count("t:Destroy()"), 1)
        for check in checks:
            with self.subTest(check=check):
                self.assertIn(check, trap)
                scoped = victim_gate if check == "t:Destroy()" else trap
                self.assertNotIn(check, scoped.replace(check, "", 1))
        self.assertLess(trap.index("fired=true"), trap.index("if not safeMove("))
        self.assertLess(trap.index("if not safeMove("), trap.index("fired=false"))
        self.assertLess(trap.index("fired=false"), trap.rindex("t:Destroy()"))

    def test_authorization_limits_and_reversibility(self):
        for value in ["MAX_CRAFT = 4", "MAX_PARTS_PER_WORLD = 95",
                      "TRAP_LIFETIME = 24", "VEHICLE_LIFETIME = 180",
                      'mode~="BATTLE_ROYALE"', "EGGRUMBLE_Eliminated",
                      "EGGRUMBLE_QueuedMode", "root.Position-part.Position",
                      "v.seat.Occupant", "world.Destroying:Connect",
                      "heartbeat:Disconnect()", "scenes[world]=nil"]:
            with self.subTest(value=value):
                self.assertIn(value, SOURCE)

    @staticmethod
    def fixture(root):
        server = {"$className": "ServerScriptService"}
        for i in range(31):
            name = ("EGGRUMBLE_LobbyCastleModesPreview" if i == 0 else
                    "EGGRUMBLE_SwarmCombat" if i == 1 else "CANONICAL_" + str(i))
            file = root / (name + ".server.luau")
            file.write_text("-- canonical source " + name + "\n")
            server[name] = {"$path": file.name}
        raw = {"name": "SOURCE_TEST_31", "tree": {"$className": "DataModel",
                                                  "ServerScriptService": server}}
        inp = root / "base31.project.json"
        inp.write_text(json.dumps(raw))
        return inp

    def test_off_and_on_is_exact(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = self.fixture(root)
            on = root / "sub" / "on32.project.json"
            off = root / "sub" / "off31.project.json"
            rec_on = mod.overlay(base, on, True)
            rec_off = mod.overlay(base, off, False)
            self.assertEqual(rec_on["source_count"], 32)
            self.assertEqual(rec_off["source_count"], 31)
            _, a = mod.flat(base)
            _, b = mod.flat(on)
            _, c = mod.flat(off)
            self.assertEqual(set(a), set(c))
            self.assertEqual(len(set(b) - set(a)), 1)
            self.assertEqual(
                {n: v.read_bytes() for n, v in a.items()},
                {n: b[n].read_bytes() for n in a})
            self.assertEqual(
                {n: v.read_bytes() for n, v in a.items()},
                {n: c[n].read_bytes() for n in a})

    def test_reject_duplicate_and_stale_base(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = self.fixture(root)
            bad = json.loads(base.read_text())
            del bad["tree"]["ServerScriptService"]["CANONICAL_30"]
            base.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, "RED_NOT_CURRENT_31"):
                mod.overlay(base, root / "bad.project.json", True)

    def test_reject_overwrite_existing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = self.fixture(root)
            with self.assertRaisesRegex(ValueError, "RED_OVERWRITE"):
                mod.overlay(base, base, True)


if __name__ == "__main__":
    unittest.main()
