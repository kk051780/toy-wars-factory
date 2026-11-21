"""Source-only regression gate: castle foundation follows the VIEW camera.

Does not claim to simulate Roblox Camera, streaming, FPS, or visual acceptance.
"""
from pathlib import Path
import unittest

SRC = Path(__file__).with_name("EGGRUMBLE_CastleFoundationMatte.client.luau")

def validate(text: str) -> None:
    start = text.find("local function eyePosition(): Vector3?")
    stop = text.find("\nend", start)
    if start < 0 or stop < 0:
        raise ValueError("RED_CAMERA_LOOKUP_FUNCTION_MISSING")
    body = text[start:stop]
    camera = "local camera = Workspace.CurrentCamera"
    first = "if camera then return camera.CFrame.Position end"
    root = 'local root = if character then character:FindFirstChild("HumanoidRootPart") else nil'
    last = 'return if root and root:IsA("BasePart") then root.Position else nil'
    for marker in (camera, first, "local character = player.Character", root, last):
        if body.count(marker) != 1:
            raise ValueError("RED_CAMERA_REQUIRED_OR_DUPLICATE_" + marker)
    if not (body.index(camera) < body.index(first)
            < body.index("local character = player.Character")
            < body.index(root) < body.index(last)):
        raise ValueError("RED_CAMERA_NOT_FIRST_OR_ROOT_FALLBACK_BROKEN")
    if body.count("return ") != 2:
        raise ValueError("RED_CAMERA_UNEXPECTED_CONTROL_FLOW")
    if text.count("local eye = eyePosition()") != 1:
        raise ValueError("RED_LOD_NOT_USING_CAMERA_EYE")
    if not (text.count("local dist = (core.Position - eye).Magnitude") == 1
            and text.count("if dist <= MAX_DISTANCE_STUDS then") == 1):
        raise ValueError("RED_LOD_PROXIMITY_BROKEN")
    for marker in ("local MAX_CASTLES = if UserInputService.TouchEnabled then 2 else 3",
                   "local PARTS_PER_CASTLE = 8",
                   "assert(count * PARTS_PER_CASTLE <= MAX_TOTAL_EXTRA_PARTS)",
                   'player:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true',
                   "stone.CanCollide = false", "stone.CanQuery = false",
                   "stone.CanTouch = false", "stone.CastShadow = false"):
        if text.count(marker) != 1:
            raise ValueError("RED_CAMERA_PATCH_SAFETY_DRIFT_" + marker)

class CameraLodTests(unittest.TestCase):
    def test_camera_first_and_avatar_fallback(self):
        validate(SRC.read_text(encoding="utf-8"))

    def test_fail_closed_mutations(self):
        original = SRC.read_text(encoding="utf-8")
        mutants = [
            ("if camera then return camera.CFrame.Position end",
             "if camera then return Vector3.zero end"),
            ("local camera = Workspace.CurrentCamera",
             "local camera = nil"),
            ("local character = player.Character",
             "local character = nil"),
            ('FindFirstChild("HumanoidRootPart")',
             'FindFirstChild("Head")'),
            ('root:IsA("BasePart")', 'root:IsA("Folder")'),
            ("then root.Position else nil", "then Vector3.zero else nil"),
            ("local eye = eyePosition()", "local eye = nil"),
            ("local dist = (core.Position - eye).Magnitude",
             "local dist = 0"),
            ("if dist <= MAX_DISTANCE_STUDS then", "if true then"),
            ("then 2 else 3", "then 20 else 30"),
            ("local PARTS_PER_CASTLE = 8", "local PARTS_PER_CASTLE = 80"),
            ("stone.CanQuery = false", "stone.CanQuery = true"),
        ]
        for before, after in mutants:
            self.assertIn(before, original)
            with self.subTest(before=before), self.assertRaises(ValueError):
                validate(original.replace(before, after, 1))
        prefix = """local function eyePosition(): Vector3?
    local character = player.Character
    local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
    if root and root:IsA("BasePart") then return root.Position end
    local camera = Workspace.CurrentCamera
    return if camera then camera.CFrame.Position else nil
end"""
        start = original.index("local function eyePosition(): Vector3?")
        end = original.index("\nend", start) + 4
        with self.assertRaises(ValueError):
            validate(original[:start] + prefix + original[end:])

if __name__ == "__main__":
    unittest.main()
