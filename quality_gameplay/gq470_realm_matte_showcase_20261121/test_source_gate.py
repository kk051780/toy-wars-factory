#!/usr/bin/env python3
"""Source-only fail-closed gate for the FB-014/015 4-realm visual A candidate.

This is not Native Luau, Rojo, Studio, Android, or a human beauty test.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "rc_fastlane/features/realm_hunt/RealmHunt.server.luau"
CLIENT = ROOT / "rc_fastlane/features/realm_hunt/RealmHuntHUD.client.luau"

def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("RED_REALM_ART_" + reason)

def server_gate(text: str) -> None:
    # Exactly four known realm IDs and exactly 4 visual pieces per world landmark.
    for marker in ('id="SKY"', 'id="SEA"', 'id="EMBER"', 'id="STAR"'):
        require(text.count(marker) == 1, "REALM_COUNT_OR_ID")
    require('local THEMES = {' in text, "FOUR_SHAPES")
    for marker in ("SKY={shape=", "SEA={shape=", "EMBER={shape=", "STAR={shape="):
        require(text.count(marker) == 1, "MISSING_SCULPT")
    require(text.count('Instance.new("Part")') == 3, "PART_CONSTRUCTORS")
    require(text.count('Instance.new("WedgePart")') == 1, "FACET_CONSTRUCTOR")
    require('folder:SetAttribute("GeneratedParts",#displays*4)' in text
            and 'folder:SetAttribute("VisualPartBudget",16)' in text, "PART_BUDGET")
    require('Enum.Material.Neon' not in text, "NEON_BALLS")
    require('billboard.AlwaysOnTop=false' in text
            and 'billboard.MaxDistance=35' in text, "SCREEN_OCCLUSION")
    require('if step<0.18 then return end' in text, "MOBILE_UPDATE_PACE")
    for marker in ('CanCollide=false', 'CanTouch=false', 'CanQuery=false',
                   'markDiscovered(player, item)', 'record.found[item.id]=true',
                   'prompt.Triggered:Connect(function(player)',
                   'if not RunService:IsStudio() then return end',
                   'Players.PlayerRemoving:Connect'):
        require(marker in text, "GAMEPLAY_GUARD_" + marker)
    require('GetService("DataStoreService")' not in text
            and 'FireServer(' not in text and 'InvokeServer(' not in text,
            "NEW_AUTHORITY")

def client_gate(text: str) -> None:
    for marker in ('GetAttribute(prefix.."Count")',
                   'GetAttribute(prefix.."Complete")',
                   'GetAttributeChangedSignal(prefix..key)',
                   'visibilityLease+=1', 'visibilityLease==mine',
                   'task.delay(duration', 'cue(complete and 6 or 4)',
                   'card.Visible=false', 'gui.ResetOnSpawn=false'):
        require(marker in text, "CUE_GUARD_" + marker)
    require('RenderStepped' not in text and 'Heartbeat:Connect' not in text,
            "PER_FRAME_CLIENT_LOOP")
    require('FireServer' not in text and 'InvokeServer' not in text,
            "CLIENT_OWNS_REWARD")
    require('heading.TextScaled=false' in text
            and 'detail.TextScaled=false' in text, "MOBILE_TEXT")
    require('card.Size=UDim2.fromOffset(136,42)' in text,
            "COMPACT_CUE")

class RealmSourceGate(unittest.TestCase):
    def test_server_source(self):
        server_gate(SERVER.read_text(encoding="utf-8"))

    def test_client_source(self):
        client_gate(CLIENT.read_text(encoding="utf-8"))

    def test_fail_closed_mutations(self):
        s = SERVER.read_text(encoding="utf-8")
        c = CLIENT.read_text(encoding="utf-8")
        cases = [
            (server_gate, s.replace('VisualPartBudget",16', 'VisualPartBudget",64')),
            (server_gate, s.replace('CanCollide=false', 'CanCollide=true')),
            (server_gate, s.replace('billboard.AlwaysOnTop=false',
                                    'billboard.AlwaysOnTop=true')),
            (server_gate, s.replace('if step<0.18 then return end',
                                    'if step<0.01 then return end')),
            (server_gate, s.replace('    core.Material=Enum.Material.SmoothPlastic',
                                    '    core.Material=Enum.Material.Neon')),
            (client_gate, c.replace('visibilityLease==mine', 'visibilityLease~=mine')),
            (client_gate, c.replace('cue(complete and 6 or 4)', 'card.Visible=true')),
            (client_gate, c + '\nRunService.RenderStepped:Connect(function() end)\n'),
        ]
        for gate, altered in cases:
            with self.subTest(gate=gate.__name__, case=cases.index((gate, altered))):
                with self.assertRaises(ValueError):
                    gate(altered)

if __name__ == "__main__":
    unittest.main(verbosity=2)
