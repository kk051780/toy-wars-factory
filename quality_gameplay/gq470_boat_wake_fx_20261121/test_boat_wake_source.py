"""Source-only, fail-closed ART gate for REAL69→70 local boat wake.
Static QA is NOT Roblox engine, human visual, mobile or formal RC PASS.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name("EGGRUMBLE_BoatWakeFX.client.luau")
LSS = ROOT / "handoffs/EGGRUMBLE-LAND-SEA-SKY-20261117/EGGRUMBLE_LandSeaSkyTraversal.server.luau"

NUMERIC = {
    "PULSE_SECONDS": "0.28",
    "LIFE_SECONDS": "0.56",
    "MIN_HORIZONTAL_SPEED": "10",
    "MAX_LIVE_PARTS": "6",
    "MAX_PARTS_PER_PULSE": "2",
    "MOBILE_PARTS_PER_PULSE": "1",
    "CAMERA_FX_DISTANCE": "96",
    "MAX_SEAT_WATER_HEIGHT": "12",
}
MANDATORY = [
    "GQ470_FB015_BOAT_WAKE_MATTE_20261121",
    "local function isSeaCraft(seat: BasePart?): boolean",
    'seat.Name ~= "PilotSeat"',
    '"^BUILDER_SEA_BOAT_%d+$"',
    '"^BEAST_SEA_BEAST_%d+$"',
    "local function waterSurface(craft: Model, sample: Vector3): Vector3?",
    '"COASTAL_WATER_VISUAL_ONLY"',
    '"OFFSHORE_NAVIGABLE_SEA_LANE"',
    "scene:FindFirstChild(name)",
    "scene:IsDescendantOf(Workspace)",
    "water.CFrame:PointToObjectSpace(sample)",
    "math.abs(localPos.X) <= maxX",
    "math.abs(localPos.Z) <= maxZ",
    "localPos.Y <= top + MAX_SEAT_WATER_HEIGHT",
    "water.CFrame:PointToWorldSpace",
    "horizontal.Magnitude < MIN_HORIZONTAL_SPEED",
    "(camera.CFrame.Position - seat.Position).Magnitude > CAMERA_FX_DISTANCE",
    "local maxPerPulse = if TOUCH then MOBILE_PARTS_PER_PULSE else MAX_PARTS_PER_PULSE",
    "MAX_LIVE_PARTS - liveParts",
    'Instance.new("WedgePart")',
    "part.Material = Enum.Material.SmoothPlastic",
    "part.Transparency = 0.54",
    "part.Anchored = true",
    "part.CanCollide = false",
    "part.CanTouch = false",
    "part.CanQuery = false",
    "part.CastShadow = false",
    "part.Destroying:Connect",
    "Debris:AddItem(part, LIFE_SECONDS + 0.05)",
    "position - lastPosition",
    "moved / PULSE_SECONDS",
    "local stern = seat.Position - forward * 9.0",
    "if waterSurface(craft, stern) == nil then return end",
    "waterSurface(craft, stern + right * (sideSign * 4.1))",
    "serial % 2 == 0",
    "math.rad(sideSign * 18)",
    "pulseSerial += 1",
    "emitWake(seat, moved / PULSE_SECONDS, pulseSerial)",
    "humanoid.SeatPart ~= seat",
    "task.delay(PULSE_SECONDS, pulse)",
    "humanoid.Seated:Connect",
    "humanoid.Died:Connect",
    "PLAYER.CharacterRemoving:Connect",
    "PLAYER.CharacterAdded:Connect",
    "generation ~= seatToken",
    "clearVisuals()",
]
FORBIDDEN = [
    "AssemblyLinearVelocity", "Workspace:Raycast", "Workspace.Terrain",
    "RemoteEvent", "RemoteFunction", "FireServer(", "InvokeServer(",
    "TakeDamage(", "DataStore", "MarketplaceService", "RenderStepped",
    "Heartbeat", "RunService", "while true", "while task.wait",
    "Enum.Material.Neon", "ParticleEmitter", "PointLight",
    "SetNetworkOwner(", "part.CanCollide = true",
    "part.CanTouch = true", "part.CastShadow = true",
]
def validate(source: str) -> bool:
    code = "\n".join(line.split("--", 1)[0] for line in source.splitlines())
    for marker in MANDATORY:
        if marker not in code:
            raise ValueError("RED_MISSING:" + marker)
    for forbidden in FORBIDDEN:
        if forbidden in code:
            raise ValueError("RED_FORBIDDEN:" + forbidden)
    for key, value in NUMERIC.items():
        if not re.search(r"(?m)^\s*local\s+" + key + r"\s*=\s*" +
                         re.escape(value) + r"\s*$", code):
            raise ValueError("RED_NUMERIC_BUDGET:" + key)
    if source.count('Instance.new("WedgePart")') != 1:
        raise ValueError("RED_MULTIPLE_PART_SITES")
    if len(source.encode()) > 9500:
        raise ValueError("RED_UNBOUNDED_SOURCE")
    return True

def validate_lss_contract(source: str) -> bool:
    """Check real historical author source — not a fabricated water/seat physics spec."""
    required = [
        'local seat=Instance.new("VehicleSeat")',
        'seat.Name="PilotSeat"',
        "seat.Anchored=true",
        "craft:PivotTo(targetCF)",
        '"COASTAL_WATER_VISUAL_ONLY"',
        '"OFFSHORE_NAVIGABLE_SEA_LANE"',
        'Enum.Material.Glass,false',
        'Vector3.new(math.min(650,floor.Size.X-95),0.14,180)',
        'local seaSpawn=Vector3.new(x-120,y+2,shoreZ+15)',
        'local start=CFrame.new(at+Vector3.new(0,3,0))',
        'seat.CFrame=start*CFrame.new(0,2.2,0)',
        'Vector3.new(9,2.3,13)',
        'start*CFrame.new(side*6,-.3,2)',
        'makeRide(p,"BUILDER","SEA_BOAT",seaSpawn)',
        'makeRide(p,"BEAST","SEA_BEAST",seaSpawn+Vector3.new(70,0,0))',
    ]
    for item in required:
        if item not in source:
            raise ValueError("RED_ORIGINAL_LSS_MISMATCH:" + item)
    return True

class TestBoatWake(unittest.TestCase):
    def test_source_contract(self):
        self.assertTrue(validate(SOURCE.read_text(encoding="utf-8")))

    def test_actual_author_movement_and_water_contract(self):
        self.assertTrue(validate_lss_contract(LSS.read_text(encoding="utf-8")))

    def test_offline_lss_ordinary_sea_spawn_wake_geometry(self):
        # NUMERIC MODEL ONLY, not Studio engine evidence. Original author:
        # 700-wide arena -> sea width=min(650,700-95)=605, depth=180;
        # seat y=2+3+2.2, water top y=0.08+0.14/2=0.15;
        # initial forward +Z, stern nine studs backward from z=+15.
        sea_half_width = min(650, 700 - 95) / 2
        sea_half_depth = 180 / 2
        water_top_y = 0.08 + 0.14 / 2
        seat_x, seat_z, seat_y = -120, 15, 2 + 3 + 2.2
        stern_z = seat_z - 9.0
        self.assertLess(seat_y - water_top_y, 12)
        for flank in (-4.1, +4.1):
            self.assertLess(abs(seat_x + flank), sea_half_width - 1)
            self.assertLess(abs(stern_z), sea_half_depth - 1)
        # A sea-adjacent airship at y+40 or a boat outside the lane
        # is excluded by the height and local water boundary tests.
        self.assertGreater(40 - water_top_y, 12)
        self.assertGreater(abs(330), sea_half_width - 1)

    def test_negative_source_mutations_rejected(self):
        original = SOURCE.read_text(encoding="utf-8")
        mutants = [
            ("local MAX_LIVE_PARTS = 6", "local MAX_LIVE_PARTS = 600"),
            ("local MOBILE_PARTS_PER_PULSE = 1", "local MOBILE_PARTS_PER_PULSE = 12"),
            ("local PULSE_SECONDS = 0.28", "local PULSE_SECONDS = 0"),
            ("local CAMERA_FX_DISTANCE = 96", "local CAMERA_FX_DISTANCE = 9600"),
            ("local MAX_SEAT_WATER_HEIGHT = 12", "local MAX_SEAT_WATER_HEIGHT = 1000"),
            ('seat.Name ~= "PilotSeat"', "false"),
            ('"^BUILDER_SEA_BOAT_%d+$"', '"^.*$"'),
            ('"^BEAST_SEA_BEAST_%d+$"', '"^.*$"'),
            ('"COASTAL_WATER_VISUAL_ONLY"', '"SEA"'),
            ('"OFFSHORE_NAVIGABLE_SEA_LANE"', '"SEA"'),
            ("scene:IsDescendantOf(Workspace)", "true"),
            ("math.abs(localPos.Z) <= maxZ", "true"),
            ("localPos.Y <= top + MAX_SEAT_WATER_HEIGHT", "true"),
            ("horizontal.Magnitude < MIN_HORIZONTAL_SPEED", "false"),
            ("position - lastPosition", "Vector3.zero"),
            ("moved / PULSE_SECONDS", "Vector3.zero"),
            ("local stern = seat.Position - forward * 9.0",
             "local stern = seat.Position - forward * 4.0"),
            ("serial % 2 == 0", "true"),
            ("sideSign * 4.1", "sideSign * 0.1"),
            ("math.rad(sideSign * 18)", "math.rad(0)"),
            ("if waterSurface(craft, stern) == nil then return end",
             "if false then return end"),
            ("waterSurface(craft, stern + right * (sideSign * 4.1))",
             "stern + right * (sideSign * 4.1)"),
            ("humanoid.SeatPart ~= seat", "false"),
            ("part.CanCollide = false", "part.CanCollide = true"),
            ("part.CastShadow = false", "part.CastShadow = true"),
            ('Instance.new("WedgePart")', 'Instance.new("Part")'),
            ("task.delay(PULSE_SECONDS, pulse)", "pulse()"),
            ("generation ~= seatToken", "false"),
            ("humanoid.Died:Connect", "humanoid.Running:Connect"),
        ]
        for before, after in mutants:
            self.assertIn(before, original)
            with self.subTest(after=after), self.assertRaises(ValueError):
                validate(original.replace(before, after))
        for extra in ("\nRunService.Heartbeat:Connect(function() end)",
                      "\nRemoteEvent:FireServer()", "\npart.CanCollide = true"):
            with self.assertRaises(ValueError):
                validate(original + extra)

    def test_negative_original_author_mutations_rejected(self):
        original = LSS.read_text(encoding="utf-8")
        for before, after in [
            ("seat.Anchored=true", "seat.Anchored=false"),
            ("craft:PivotTo(targetCF)", "craft:MoveTo(point)"),
            ('"COASTAL_WATER_VISUAL_ONLY"', '"NONE"'),
            ('makeRide(p,"BUILDER","SEA_BOAT",seaSpawn)', 'makeRide(p,"BUILDER","AIRSHIP",seaSpawn)'),
        ]:
            self.assertIn(before, original)
            with self.subTest(before=before), self.assertRaises(ValueError):
                validate_lss_contract(original.replace(before, after))

if __name__ == "__main__":
    unittest.main()
