"""Fail-closed source contracts for optional GQ respawn fairness.
Do not call these real Roblox Studio gameplay tests.
"""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "EGGRUMBLE_RespawnGrace.server.luau"
PROJECT = ROOT / "EGGRUMBLE_V3_RESPAWN_GRACE.project.json"
SOURCE = SCRIPT.read_text(encoding="utf-8")
TREE = json.loads(PROJECT.read_text(encoding="utf-8"))["tree"]


class RespawnGraceContracts(unittest.TestCase):
    def test_actual_server_script_not_a_mock(self):
        self.assertTrue(SCRIPT.name.endswith(".server.luau"))
        self.assertIn('Instance.new("ForceField")', SOURCE)
        self.assertIn('shield.Parent = character', SOURCE)
        self.assertIn('if not RunService:IsStudio() then return end', SOURCE)

    def test_original_author_21_scripts_are_reused_not_copied(self):
        paths = []
        def walk(node):
            if not isinstance(node, dict):
                return
            if "$path" in node:
                paths.append((ROOT / node["$path"]).resolve(strict=True))
                return
            for key, child in node.items():
                if not key.startswith("$"):
                    walk(child)
        walk(TREE)
        self.assertEqual(len(paths), 22)
        self.assertEqual(len(set(paths)), 22)
        ours = [p for p in paths if p.parent == ROOT]
        originals = [p for p in paths if p.parent != ROOT]
        self.assertEqual(ours, [SCRIPT])
        self.assertEqual(len(originals), 21)
        self.assertTrue(all("P0D-PQG-SEVEN-HERO-PLAYABLE-20261116" in str(p) for p in originals))

    def test_authoritative_arena_scope(self):
        for snippet in ('player.Parent ~= Players',
                        'player.Character ~= character',
                        'player:GetAttribute("EGGRUMBLE_QueuedMode")',
                        'mode ~= "TEAM" and mode ~= "BATTLE_ROYALE"',
                        'mode .. "_Arena"',
                        'Castle_" .. tostring(player.UserId)',
                        'StandardCore',
                        'FALLEN_CORE_COLOR'):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, SOURCE)

    def test_only_real_character_within_home_bounded(self):
        for snippet in ('MAX_HOME_DISTANCE = 85',
                        '(root.Position - core.Position).Magnitude > MAX_HOME_DISTANCE',
                        'human.Health <= 0',
                        'root:IsA("BasePart")'):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, SOURCE)

    def test_no_protection_in_lobby_or_eliminated(self):
        self.assertIn('player:GetAttribute("EGGRUMBLE_Eliminated") == true', SOURCE)
        self.assertIn('if not arena then return nil end', SOURCE)
        self.assertIn('if not castle or not castle:IsA("Model")', SOURCE)

    def test_2_25_second_life_only_and_bounded(self):
        self.assertIn('GRACE_SECONDS = 2.25', SOURCE)
        self.assertIn('task.delay(GRACE_SECONDS, revoke)', SOURCE)
        self.assertIn('while live[player] == state and os.clock() < deadline do', SOURCE)
        self.assertIn('task.wait(0.1)', SOURCE)
        self.assertIn('if live[player] == state then clear(player) end', SOURCE)

    def test_attack_tool_breaks_grace(self):
        self.assertIn('character.ChildAdded:Connect', SOURCE)
        self.assertIn('if instance:IsA("Tool") then revoke() end', SOURCE)
        self.assertIn('for _, instance in ipairs(character:GetChildren()) do', SOURCE)

    def test_any_gameplay_prompt_breaks_grace(self):
        self.assertIn('ProximityPromptService.PromptTriggered:Connect', SOURCE)
        self.assertIn('clear(player)', SOURCE)

    def test_leaving_dying_or_round_end_clears_own_forcefield(self):
        for snippet in ('humanoid.Died:Connect(revoke)',
                        'player.CharacterRemoving:Connect',
                        'Players.PlayerRemoving:Connect(clear)',
                        'EGGRUMBLE_QueuedMode',
                        'EGGRUMBLE_Eliminated',
                        'state.shield:Destroy()'):
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, SOURCE)

    def test_never_destroy_external_forcefield(self):
        self.assertIn('character:FindFirstChildOfClass("ForceField")', SOURCE)
        self.assertIn('if state.shield.Parent then state.shield:Destroy() end', SOURCE)
        self.assertNotIn('for _, force in ipairs(character:GetChildren())', SOURCE)

    def test_no_client_authority_eggs_economy_or_networking(self):
        for word in ('FireServer(', 'InvokeServer(', 'RemoteEvent', 'DataStore',
                     'MarketplaceService', 'TakeDamage(', 'Rules.damageCastle',
                     'Rules.depositEggs', 'Rules.takeFieldEgg', 'SetAttribute(',
                     'TeleportService', 'PlayerGui'):
            with self.subTest(word=word):
                self.assertNotIn(word, SOURCE)

    def test_no_persistent_global_forcefield(self):
        self.assertNotIn('SpawnLocation', SOURCE)
        self.assertNotIn('ForceField.Visible = true', SOURCE)
        self.assertIn('live[player] = state', SOURCE)
        self.assertIn('live[player] = nil', SOURCE)


    def test_genuine_server_died_required(self):
        self.assertIn('humanoid.Died:Connect(function()', SOURCE)
        self.assertIn('tickets[player] = {', SOURCE)
        self.assertIn('local function currentArena(player: Player, character: Model)', SOURCE)
        self.assertIn('if not ticket or os.clock() > ticket.expiresAt then return end', SOURCE)

    def test_death_ticket_single_use(self):
        self.assertIn('tickets[player] = nil\n            if not ticket', SOURCE)
        self.assertIn('RESPAWN_TICKET_SECONDS = 12', SOURCE)
        self.assertIn('expiresAt = os.clock() + RESPAWN_TICKET_SECONDS', SOURCE)

    def test_rejects_new_round_same_mode(self):
        self.assertIn('currentArena(player, character) ~= ticket.arena', SOURCE)
        self.assertIn('player:GetAttribute("EGGRUMBLE_QueuedMode") ~= ticket.mode', SOURCE)

    def test_original_character_death_not_stubbed_by_initial_spawn(self):
        self.assertIn('if player.Character then bindCharacter(player.Character) end', SOURCE)
        self.assertIn('if player.Character ~= character then return end', SOURCE)
        self.assertIn('local ticket = tickets[player]', SOURCE)
        self.assertIn('if not ticket or os.clock() > ticket.expiresAt then return end', SOURCE)

    def test_all_tickets_cleared_on_player_departure(self):
        self.assertIn('Players.PlayerRemoving:Connect(function(player: Player)', SOURCE)
        self.assertIn('tickets[player] = nil\n    clear(player)', SOURCE)
        self.assertIn('player.CharacterRemoving:Connect(function()', SOURCE)
        self.assertIn('local ticket = tickets[player]', SOURCE)


if __name__ == "__main__":
    unittest.main()
