"""Offline PREP/source-lock checks; NOT an engine playtest or a TTS request."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "rc_fastlane" / "features" / "talking_npc"
LOCK = FEATURE / "PREP_SOURCE_LOCK.json"


class TalkingNpcPrepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = json.loads(LOCK.read_text(encoding="utf-8"))
        cls.sources = {
            name: (FEATURE / name).read_text(encoding="utf-8")
            for name in cls.lock["files"]
        }

    def test_source_bytes_match_pinned_git_blobs(self):
        self.assertEqual(self.lock["schema"], "P0D_TALKING_NPC_PREP_SOURCE_LOCK_V1")
        self.assertTrue(self.lock["canonical_rc_unmodified"])
        self.assertFalse(self.lock["runtime_enabled_in_rc"])
        for filename, sha in self.lock["files"].items():
            raw = (FEATURE / filename).read_bytes()
            digest = hashlib.sha1(
                b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
            ).hexdigest()
            self.assertEqual(digest, sha, filename)

    def test_no_second_game_or_remote_or_paid_write(self):
        forbidden = (
            'Instance.new("RemoteEvent")',
            "DataStoreService", "UpdateAsync(", "GetDataStore(",
            "PromptProductPurchase(", "MarketplaceService",
            "TakeDamage(", "FireServer(", "OnServerEvent:Connect(",
            "os.execute(", "HttpService", "GetAsync(", "PostAsync(",
        )
        for filename, source in self.sources.items():
            for token in forbidden:
                self.assertNotIn(token, source, f"{filename}: {token}")

    def test_server_private_observation_and_shutdown(self):
        s = self.sources["TalkingNPCRuntime.server.luau"]
        for fragment in (
            'if not RunService:IsStudio() then return end',
            'ServerStorage:GetAttribute(FLAG) ~= true',
            'workspace:Raycast',  # case-sensitive environment guard below
        ):
            if fragment == 'workspace:Raycast':
                self.assertIn('Workspace:Raycast', s)
            else:
                self.assertIn(fragment, s)
        self.assertIn("params.FilterDescendantsInstances", s)
        self.assertIn("d.Magnitude <= 45", s)
        self.assertIn("remote:FireClient(player,", s)
        self.assertIn('if team and not inTeam(player, team) then return end', s)
        self.assertIn("facts.itemKnownByTeam = true", s)
        self.assertIn("facts.hintUnlocked", s)
        self.assertNotIn("remote:FireAllClients", s)

    def test_short_safe_dialogue_and_cooldown(self):
        s = self.sources["TalkingNPCDirector.luau"]
        for intent in (
            '"ENEMY_ALERT"', '"EGG_RETURN"', '"KNOWN_ITEM"',
            '"SECRET_HINT"', '"TRICK_RUMOR"', '"HELLO"', '"INTRO"',
        ):
            self.assertIn(intent, s)
        self.assertIn("observedByTeam == true", s)
        self.assertIn("itemKnownByTeam == true", s)
        self.assertIn("hintUnlocked == true", s)
        self.assertIn("local gap = urgent == true and 15 or 30", s)
        self.assertIn("isGeneratedAI = false", s)

    def test_tts_is_optional_subtitles_always_visible(self):
        s = self.sources["TalkingNPCClient.client.luau"]
        for token in (
            'Instance.new("AudioTextToSpeech")',
            'Instance.new("AudioDeviceOutput")',
            'Instance.new("Wire")',
            'VoiceToggle', 'AudioTextToSpeech',
            'tts:LoadAsync()', 'tts:Play()',
            'message.Text = packet.text',
            'not audioEnabled', 'pcall(', 'Caption',
        ):
            if token == "Caption":
                self.assertIn("caption", s.lower()) if "caption" in s.lower() else self.assertIn("subtitles", s.lower())
            else:
                self.assertIn(token, s)
        self.assertIn('packet.kind ~= "P0D_NPC_TALK_V1"', s)
        self.assertIn('type(packet.text) ~= "string"', s)


if __name__ == "__main__":
    unittest.main()
