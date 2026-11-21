"""Local-only spawn arrival source guard: fail closed on budget/authority/lifecycle changes."""
from pathlib import Path
import unittest
import re
SRC = Path(__file__).with_name("EGGRUMBLE_SpawnArrivalArt.client.luau")
def validate(s):
    markers = [
        "local MAX_EMIT_TOUCH = 5", "local MAX_EMIT_DESKTOP = 9",
        "local EFFECT_SECONDS = 0.82", "local ROOT_TIMEOUT_SECONDS = 5",
        "generation ~= token or player.Character ~= character",
        'if not root or not root:IsA("BasePart") then return end',
        'human.Health <= 0 then return end', 'glow.DepthMode = Enum.HighlightDepthMode.Occluded',
        "glow.FillTransparency = 0.84", "glow.OutlineTransparency = 0.46",
        "sparks.Rate = 0", "sparks.LightEmission = 0",
        "Debris:AddItem(foot, EFFECT_SECONDS)", "Debris:AddItem(folder, EFFECT_SECONDS)",
        'player.CharacterRemoving:Connect', 'player.CharacterAdded:Connect',
        "if player.Character then onCharacter(player.Character) end",
    ]
    for p in markers:
        found = (len(re.findall(r"(?m)^" + re.escape(p) + r"\s*$", s))
                 if p.startswith("local ") else s.count(p))
        if found != 1:
            raise ValueError("RED_SPAWN_ART_CONTRACT_" + p)
    for forbidden in ("RemoteEvent", "RemoteFunction", "FireServer", "InvokeServer",
                      "DataStore", "TakeDamage", "RenderStepped", "Heartbeat",
                      "while true", "Enum.Material.Neon", 'Instance.new("Part")',
                      "CharacterAutoLoads", "LoadCharacter", "SpawnLocation"):
        if forbidden in "\n".join(line.split("--",1)[0] for line in s.splitlines()):
            raise ValueError("RED_SPAWN_ART_UNSAFE_" + forbidden)
    if s.count('Instance.new("ParticleEmitter")') != 1 or s.count('Instance.new("Highlight")') != 1 or len(s.encode())>7000:
        raise ValueError("RED_SPAWN_ART_FACTORY_OR_SIZE")
class SpawnSourceTests(unittest.TestCase):
    def test_source(self):
        validate(SRC.read_text())
    def test_mutants(self):
        s=SRC.read_text()
        for before,after in [
            ("MAX_EMIT_TOUCH = 5","MAX_EMIT_TOUCH = 50"),
            ("MAX_EMIT_DESKTOP = 9","MAX_EMIT_DESKTOP = 90"),
            ("EFFECT_SECONDS = 0.82","EFFECT_SECONDS = 82"),
            ("ROOT_TIMEOUT_SECONDS = 5","ROOT_TIMEOUT_SECONDS = 500"),
            ("sparks.Rate = 0","sparks.Rate = 100"),
            ("sparks.LightEmission = 0","sparks.LightEmission = 1"),
            ("glow.FillTransparency = 0.84","glow.FillTransparency = 0"),
            ("glow.OutlineTransparency = 0.46","glow.OutlineTransparency = 0"),
            ("Debris:AddItem(foot, EFFECT_SECONDS)","Debris:AddItem(foot, 999)"),
            ("Debris:AddItem(folder, EFFECT_SECONDS)","Debris:AddItem(folder, 999)"),
            ("player.CharacterRemoving:Connect","player.X:Connect"),
            ("generation ~= token or player.Character ~= character","false"),
            ("human.Health <= 0 then return end","false then return end"),
        ]:
            self.assertIn(before,s)
            with self.subTest(before=before), self.assertRaises(ValueError):
                validate(s.replace(before,after))
        for bad in ('FireServer()', 'Instance.new("Part")', 'RunService.Heartbeat:Connect'):
            with self.assertRaises(ValueError): validate(s+"\n"+bad)
if __name__=="__main__":
    unittest.main()
