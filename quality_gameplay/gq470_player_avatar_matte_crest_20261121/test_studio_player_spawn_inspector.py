"""Studio-only diagnostic noninvasive gate; zero production selected-source edits."""
from pathlib import Path
import re
import unittest

SOURCE=Path(__file__).with_name("StudioPlayerSpawnInspector.client.luau")

def errors(source):
    lines=[s.split("--",1)[0] for s in source.splitlines()]
    code="\n".join(lines)
    must=[
        "if not RunService:IsStudio() then return end",
        "local MAX_PROBES = 30",
        "local PROBE_SECONDS = 1",
        "player.CharacterAdded:Connect",
        "player.CharacterRemoving:Connect",
        "joined:Disconnect()",
        "removing:Disconnect()",
        "camera.CameraSubject",
        "part.LocalTransparencyModifier > 0.95",
        "cameraDistance >= 5",
        "hiddenLocally / visibleTotal >= 0.66",
        "SOURCE_STATE_APPEARS_VALID_ENGINE_VISUAL_STILL_NEEDS_OWNER",
    ]
    bad=[]
    for x in must:
        if x not in code: bad.append("missing:"+x)
    for pattern in [
        r':LoadCharacter\s*\(',r'\bCharacterAutoLoads\s*=',
        r'\.Health\s*=',r'\.CFrame\s*=',r'\.Transparency\s*=',
        r'Instance\.new\s*\(',r'\bFireServer\s*\(',r'\bInvokeServer\s*\(',
        r'\bGetService\(["\'](?:DataStoreService|MarketplaceService|TeleportService)["\']\)',
        r'\b(?:Heartbeat|RenderStepped):Connect\s*\(',
    ]:
        if re.search(pattern,code): bad.append("forbidden:"+pattern)
    return bad

class StudioInspectorSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.source=SOURCE.read_text()

    def test_no_game_authority_or_publish_scripts(self):
        self.assertFalse(errors(self.source),errors(self.source))

    def test_first_person_false_positive_excluded(self):
        self.assertIn("cameraDistance >= 5",self.source)
        self.assertIn("visibleTotal >= 3",self.source)

    def test_bounded_cleanup(self):
        self.assertIn("for i = 1, MAX_PROBES do",self.source)
        self.assertIn("joined:Disconnect()",self.source)
        self.assertIn("removing:Disconnect()",self.source)

    def test_five_fatal_mutants_blocked(self):
        mutants=[
            self.source.replace("if not RunService:IsStudio() then return end","",1),
            self.source.replace("local MAX_PROBES = 30","local MAX_PROBES = 999999",1),
            self.source.replace("joined:Disconnect()","-- missing teardown",1),
            self.source.replace("cameraDistance >= 5","cameraDistance >= 0",1),
            self.source + "\nplayer:LoadCharacter()",
        ]
        for i,mutant in enumerate(mutants):
            with self.subTest(i=i):
                self.assertTrue(errors(mutant),f"unsafe mutation{i} was accepted")

if __name__=="__main__":
    unittest.main()
