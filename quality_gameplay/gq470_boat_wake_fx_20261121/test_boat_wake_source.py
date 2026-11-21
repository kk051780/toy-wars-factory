"""Fail-closed static contract for a client-only Terrain boat wake A candidate.
This does not assert Studio/Android performance or #420 art acceptance.
"""
from pathlib import Path
import unittest
import re
SOURCE = Path(__file__).with_name("EGGRUMBLE_BoatWakeFX.client.luau")
MANDATORY = [
    "GQ470_FB015_BOAT_WAKE_MATTE_20261121",
    "local PULSE_SECONDS = 0.28",
    "local LIFE_SECONDS = 0.56",
    "local MIN_HORIZONTAL_SPEED = 10",
    "local MAX_LIVE_PARTS = 6",
    "local MAX_PARTS_PER_PULSE = 2",
    "local MOBILE_PARTS_PER_PULSE = 1",
    "local CAMERA_FX_DISTANCE = 96",
    "local WATER_RAY_LENGTH = 13",
    "humanoid.Seated:Connect",
    "humanoid.SeatPart ~= seat",
    "seat.AssemblyLinearVelocity",
    "flat.Magnitude < MIN_HORIZONTAL_SPEED",
    "Workspace:Raycast",
    "params.IgnoreWater = false",
    "hit.Instance ~= Workspace.Terrain",
    "hit.Material ~= Enum.Material.Water",
    "hit.Normal.Y < 0.6",
    "MAX_LIVE_PARTS - liveParts",
    'Instance.new("WedgePart")',
    "part.Material = Enum.Material.SmoothPlastic",
    "part.CanCollide = false",
    "part.CanTouch = false",
    "part.CanQuery = false",
    "part.CastShadow = false",
    "Debris:AddItem",
    "task.delay(PULSE_SECONDS, pulse)",
    "generation ~= seatToken",
    "PLAYER.CharacterRemoving:Connect",
    "humanoid.Died:Connect",
    "clearVisuals()",
]
FORBIDDEN = [
    "RemoteEvent", "RemoteFunction", "FireServer(", "InvokeServer(",
    "TakeDamage(", "DataStore", "MarketplaceService",
    "RenderStepped", "Heartbeat", "RunService", "while true",
    "Enum.Material.Neon", "ParticleEmitter", "PointLight",
    "SetNetworkOwner(", "part.CanCollide = true",
]
def validate(source):
    code = "\n".join(line.split("--",1)[0] for line in source.splitlines())
    for marker in MANDATORY:
        if marker not in code: raise ValueError("RED_MISSING:"+marker)
    for forbidden in FORBIDDEN:
        if forbidden in code: raise ValueError("RED_FORBIDDEN:"+forbidden)
    # Prefix-based checks alone would erroneously accept "6" -> "600".
    numeric = {"PULSE_SECONDS":"0.28", "LIFE_SECONDS":"0.56",
        "MIN_HORIZONTAL_SPEED":"10", "MAX_LIVE_PARTS":"6",
        "MAX_PARTS_PER_PULSE":"2", "MOBILE_PARTS_PER_PULSE":"1",
        "CAMERA_FX_DISTANCE":"96", "WATER_RAY_LENGTH":"13"}
    for key, value in numeric.items():
        if not re.search(r"(?m)^\s*local\s+" + key + r"\s*=\s*" +
                         re.escape(value) + r"\s*$", code):
            raise ValueError("RED_NUMERIC_BUDGET:"+key)
    if source.count('Instance.new("WedgePart")') != 1:
        raise ValueError("RED_MULTIPLE_PART_SITES")
    if len(source.encode()) > 9300:
        raise ValueError("RED_UNBOUNDED_SOURCE")
    return True
class TestBoatWake(unittest.TestCase):
    def test_contract(self): self.assertTrue(validate(SOURCE.read_text()))
    def test_negative_mutations(self):
        src = SOURCE.read_text()
        for before, after in [
            ("local MAX_LIVE_PARTS = 6","local MAX_LIVE_PARTS = 600"),
            ("local MOBILE_PARTS_PER_PULSE = 1","local MOBILE_PARTS_PER_PULSE = 8"),
            ("local PULSE_SECONDS = 0.28","local PULSE_SECONDS = 0"),
            ("local CAMERA_FX_DISTANCE = 96","local CAMERA_FX_DISTANCE = 10000"),
            ("hit.Instance ~= Workspace.Terrain","false"),
            ("hit.Material ~= Enum.Material.Water","false"),
            ("params.IgnoreWater = false","params.IgnoreWater = true"),
            ("hit.Normal.Y < 0.6","false"),
            ("part.CanCollide = false","part.CanCollide = true"),
            ("part.CastShadow = false","part.CastShadow = true"),
            ("task.delay(PULSE_SECONDS, pulse)","pulse()"),
            ("generation ~= seatToken","false"),
            ("humanoid.SeatPart ~= seat","false"),
            ('Instance.new("WedgePart")','Instance.new("Part")'),
            ("humanoid.Died:Connect","humanoid.Running:Connect"),
        ]:
            self.assertIn(before, src)
            with self.subTest(mutant=after),self.assertRaises(ValueError):
                validate(src.replace(before,after))
        for injected in ("\nRunService.Heartbeat:Connect(function() end)",
                         "\nRemoteEvent:FireServer()", "\npart.CanCollide = true"):
            with self.assertRaises(ValueError): validate(src+injected)
if __name__=="__main__": unittest.main()
