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


    def test_sourcery_egg_and_observation_regressions(self):
        server = self.sources["TalkingNPCRuntime.server.luau"]
        self.assertIn('head:FindFirstChild("S1_CARRIED_EGG")', server)
        self.assertIn('mode == "AUTO_ENEMY_ALERT"', server)
        self.assertIn('mode ~= "AUTO_ENEMY_ALERT"', server)
        self.assertIn('== "ENEMY_ALERT" then', server)
        self.assertIn('lastAlertTarget[player] = enemy.UserId', server)
        self.assertIn('player:GetAttribute("P0D_StarShardComplete") ~= true', server)
        self.assertIn('local perSpeaker = speechTimes[player] or {}', server)
        self.assertIn('perSpeaker[speaker] = now', server)
        self.assertNotIn('lastSpeech[player] = now', server)

    def test_sourcery_hot_flag_and_module_fail_closed(self):
        server = self.sources["TalkingNPCRuntime.server.luau"]
        client = self.sources["TalkingNPCClient.client.luau"]
        self.assertIn('if not directorModule or not directorModule:IsA("ModuleScript") then', server)
        self.assertIn('pcall(require, directorModule)', server)
        self.assertIn('GetAttributeChangedSignal(FLAG):Connect(reconcile)', server)
        self.assertIn('prior.folder:Destroy()', server)
        self.assertIn('ReplicatedStorage:SetAttribute(PUBLIC_ENABLED, false)', server)
        self.assertIn('ReplicatedStorage:SetAttribute(PUBLIC_ENABLED, true)', server)
        self.assertIn('GetAttributeChangedSignal(PUBLIC_ENABLED):Connect(setEnabled)', client)
        self.assertIn('if not gui.Enabled then return end', client)
        self.assertIn('card.Visible = false', client)

    def test_sourcery_tts_single_worker_cleanup_and_budget(self):
        client = self.sources["TalkingNPCClient.client.luau"]
        self.assertIn('if audioBusy then return end', client)
        self.assertIn('audioBusy = true', client)
        self.assertIn('audioPending = nil', client)
        self.assertIn('request.nonce == speechSerial', client)
        self.assertIn('TTS_GAP = 20', client)
        self.assertIn('for _, item in ipairs(staged) do', client)
        self.assertIn('item:Destroy()', client)
        self.assertIn('if not audioEnabled then stopVoice() end', client)
        self.assertIn('audioEnabled = not audioEnabled', client)
        self.assertIn('card.Visible = true', client)
        self.assertIn('if packet.automated ~= true then', client)
        self.assertEqual(client.count('tts:LoadAsync()'), 1)

    def test_overlay_immutable_transaction_and_realms_dependency(self):
        source = (ROOT / "rc_fastlane" / "apply_talking_npc.py").read_text("utf8")
        self.assertIn('shutil.copytree(dist, staged)', source)
        self.assertIn('os.replace(staged, output_dist)', source)
        self.assertIn('shutil.rmtree(temp_root, ignore_errors=True)', source)
        self.assertIn('REQUIRE_REALM_HUNT_DIALOGUE', source)
        self.assertIn('REALM_HUNT_NOT_ENABLED', source)
        self.assertIn('OUTPUT_DIST_REQUIRED_FOR_IMMUTABLE_PREVIEW', source)
        self.assertIn('output_dist.exists()', source)


    def test_shards_only_if_unclaimed_and_realm_label_is_correct(self):
        runtime = self.sources["TalkingNPCRuntime.server.luau"]
        director = self.sources["TalkingNPCDirector.luau"]
        self.assertIn('local shardCount = player:GetAttribute("P0D_StarShardCount")', runtime)
        self.assertIn('type(shardCount) == "number" and shardCount < 6', runtime)
        self.assertIn('facts.areaCode = "star_bridge"', runtime)
        self.assertIn('star_bridge = "星降る橋"', director)
        self.assertIn('area .. "に" .. item .. "があるよ！"', director)

    def test_expired_captions_cancel_stale_audio(self):
        client = self.sources["TalkingNPCClient.client.luau"]
        receive = client.split("local function receive(packet)", 1)[1].split(
            "remote.OnClientEvent:Connect(receive)", 1)[0]
        self.assertIn("card.Visible = true", receive)
        self.assertIn("speechSerial += 1 -- invalidate any TTS LoadAsync", receive)
        self.assertIn("stopVoice()", receive)
        self.assertIn("and card.Visible then", client)
        self.assertIn("audioEnabled = not audioEnabled", client)


if __name__ == "__main__":
    unittest.main()
