#!/usr/bin/env python3
"""Fail closed static contract; gameplay engine still NOT_TESTED."""
from pathlib import Path
import unittest
SOURCE=Path(__file__).with_name("EGGRUMBLE_CameraRebind.client.luau")
must=[
'local RECOVERY_WINDOW_SECONDS = 4',
'local RETRY_SECONDS = {0.10, 0.35, 0.80, 1.70, 3.20}',
'if subject == nil then return true end',
'if subject:IsA("Seat") or subject:IsA("VehicleSeat") then return false end',
'previousOwnHumanoid ~= nil and subject == previousOwnHumanoid',
'return not subject:IsDescendantOf(game)',
'if player.Character ~= character or character.Parent == nil then return end',
'if humanoid.Parent ~= character or humanoid.Health <= 0 then return end',
'if camera.CameraType ~= Enum.CameraType.Custom then return end',
'if not lostOwnSubject(camera.CameraSubject, character) then return end',
'camera.CameraSubject = humanoid',
'if generation ~= token or os.clock() - started > RECOVERY_WINDOW_SECONDS then return end',
'task.delay(seconds, function()',
'player.CharacterRemoving:Connect(function(character: Model)',
'player.CharacterAdded:Connect(onCharacterAdded)',
'task.defer(onCharacterAdded, player.Character)',
]
forbidden=[
'CameraType =','camera.CFrame =','RenderStepped','Heartbeat','while true',
'RemoteEvent','FireServer','InvokeServer','DataStore','LoadCharacter',
'Instance.new(','ScreenGui','Highlight','TweenService','SetAttribute',
'humanoid.Health =','CanCollide =','CurrentCamera =','workspace.Gravity'
]
def validate(s):
    for marker in must:
        if s.count(marker)!=1: raise ValueError("RED_CAMERA_CONTRACT_"+marker)
    code="\n".join(line.split("--",1)[0] for line in s.splitlines())
    for marker in forbidden:
        if marker in code: raise ValueError("RED_CAMERA_SCOPE_"+marker)
    if len(s.encode())>5400:raise ValueError("RED_CAMERA_SOURCE_BUDGET")
class Gate(unittest.TestCase):
    def test_source(self): validate(SOURCE.read_text())
    def test_mutations(self):
        s=SOURCE.read_text()
        changes=[
            ('RECOVERY_WINDOW_SECONDS = 4','RECOVERY_WINDOW_SECONDS = 400'),
            ('0.10, 0.35, 0.80, 1.70, 3.20','0, 0, 0, 0, 0'),
            ('if subject == nil then return true end','if subject == nil then return false end'),
            ('if subject:IsA("Seat") or subject:IsA("VehicleSeat") then return false end','if false then return false end'),
            ('previousOwnHumanoid ~= nil','false'),
            ('return not subject:IsDescendantOf(game)','return true'),
            ('player.Character ~= character','player.Character == character'),
            ('humanoid.Health <= 0','humanoid.Health < 0'),
            ('camera.CameraType ~= Enum.CameraType.Custom','camera.CameraType == Enum.CameraType.Custom'),
            ('if not lostOwnSubject(camera.CameraSubject, character) then return end','if false then return end'),
            ('camera.CameraSubject = humanoid','camera.CameraSubject = nil'),
            ('generation ~= token','generation == token'),
            ('os.clock() - started > RECOVERY_WINDOW_SECONDS','false'),
        ]
        for a,b in changes:
            self.assertIn(a,s)
            with self.subTest(a=a),self.assertRaises(ValueError):validate(s.replace(a,b))
        for evil in ['camera.CameraType = Enum.CameraType.Custom','Instance.new("Highlight")','player:LoadCharacter()']:
            with self.subTest(evil=evil),self.assertRaises(ValueError):validate(s+"\n"+evil)
if __name__=="__main__":unittest.main()
