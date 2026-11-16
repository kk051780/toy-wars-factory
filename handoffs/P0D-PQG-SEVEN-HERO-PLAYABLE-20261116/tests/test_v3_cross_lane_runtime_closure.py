"""V3 battle dependency-closure regression, without duplicating feature writers.

Confirms existing author SevenRoleCombat/SwarmCombat/AIBots/Lobby loads
in one Studio source project. SOURCE ONLY; NOT engine runtime acceptance.
"""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
PROJECT=(ROOT/"EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8")
REGEX=re.compile(r'script\.Parent:WaitForChild\("([^"]+)"\)')
ROLE=(ROOT/"EGGRUMBLE_SevenRoleCombat.luau").read_text(encoding="utf-8")
SWARM=(ROOT/"EGGRUMBLE_SwarmCombat.luau").read_text(encoding="utf-8")
BOT=(ROOT/"EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")
LOBBY=(ROOT/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")

def problems(project=PROJECT,role=ROLE,swarm=SWARM,bot=BOT,lobby=LOBB):
    root=json.loads(project)["tree"]
    server=root["ServerScriptService"]
    mapped={k:v["$path"] for k,v in server.items() if k!="$className"}
    script_sources={
        "EGGRUMBLE_SevenRoleCombat":role,
        "EGGRUMBLE_SwarmCombat":swarm,
        "EGGRUMBLE_BotActors":bot,
        "EGGRUMBLE_LobbyCastleModesPreview":lobby,
    }
    # For every mapped server module, discover sibling dependencies dynamically.
    # This catches future original-author additions without hard-coding 7 roles.
    for module,path in mapped.items():
        if module not in script_sources:
            script_sources[module]=(ROOT/path).read_text(encoding="utf-8") if (ROOT/path).is_file() else ""
    missing=[]
    for module,src in script_sources.items():
        for req in REGEX.findall(src):
            if req not in mapped:
                missing.append(f"unwired:{module}:{req}")
    checks={
       "14 real server scripts":len(mapped)==14,
       "genuine attack shape source":mapped.get("EGGRUMBLE_AttackGeometry")=="EGGRUMBLE_AttackGeometry.luau",
       "genuine attacker/KO source":mapped.get("EGGRUMBLE_ImpactFeedback")=="EGGRUMBLE_ImpactFeedback.luau",
       "original item author intact":mapped.get("EGGRUMBLE_FieldItemPickups")=="EGGRUMBLE_FieldItemPickups.luau",
       "replay and score owner code intact":"EGGRUMBLE_RoundReplay" in mapped and "EGGRUMBLE_MatchResultService" in mapped,
       "original neutral geometry require":'WaitForChild("EGGRUMBLE_AttackGeometry")' in swarm,
       "original seven-role geometry require":'WaitForChild("EGGRUMBLE_AttackGeometry")' in role,
       "original seven-role server impact":'WaitForChild("EGGRUMBLE_ImpactFeedback")' in role,
       "original neutral real KO feedback":'ImpactFeedback.ko(' in swarm,
       "original server actual hit feedback":'ImpactFeedback.attacker(' in role,
       "single authentic V3 host":"EGGRUMBLE_LobbyCastleModesPreview" in mapped and "EGGRUMBLE_FieldItemPreview" not in mapped,
       "source presence":all((ROOT/p).is_file() for p in mapped.values()),
       "no unauthorized client script in ServerScriptService":all(not p.endswith(".client.luau") for p in mapped.values()),
       "actual V3 item session":'FieldItems.start(session,itemPositions)' in lobby,
    }
    missing.extend(k for k,v in checks.items() if not v)
    return missing

class TestCrossLaneDependencies(unittest.TestCase):
    def test_all_dependencies_closed(self):
        self.assertEqual([],problems())
    def test_neutral_geometry_unwired(self):
        p=json.loads(PROJECT)
        p["tree"]["ServerScriptService"].pop("EGGRUMBLE_AttackGeometry")
        self.assertIn("unwired:EGGRUMBLE_SwarmCombat:EGGRUMBLE_AttackGeometry",problems(project=json.dumps(p)))
    def test_hero_impact_unwired(self):
        p=json.loads(PROJECT)
        p["tree"]["ServerScriptService"].pop("EGGRUMBLE_ImpactFeedback")
        self.assertIn("unwired:EGGRUMBLE_SevenRoleCombat:EGGRUMBLE_ImpactFeedback",problems(project=json.dumps(p)))
    def test_pathrouter_unwired(self):
        p=json.loads(PROJECT)
        p["tree"]["ServerScriptService"].pop("EGGRUMBLE_BotPathRouter")
        self.assertIn("unwired:EGGRUMBLE_BotActors:EGGRUMBLE_BotPathRouter",problems(project=json.dumps(p)))
    def test_lobby_items_unwired(self):
        p=json.loads(PROJECT)
        p["tree"]["ServerScriptService"].pop("EGGRUMBLE_FieldItemPickups")
        self.assertIn("unwired:EGGRUMBLE_LobbyCastleModesPreview:EGGRUMBLE_FieldItemPickups",problems(project=json.dumps(p)))
    def test_lobby_replay_unwired(self):
        p=json.loads(PROJECT)
        p["tree"]["ServerScriptService"].pop("EGGRUMBLE_RoundReplay")
        self.assertIn("unwired:EGGRUMBLE_LobbyCastleModesPreview:EGGRUMBLE_RoundReplay",problems(project=json.dumps(p)))
    def test_new_future_role_require_detected(self):
        self.assertIn("unwired:EGGRUMBLE_SevenRoleCombat:SomeFutureMissing",
          problems(role=ROLE+'\\nlocal missed=require(script.Parent:WaitForChild("SomeFutureMissing"))'))
    def test_new_future_horde_require_detected(self):
        self.assertIn("unwired:EGGRUMBLE_SwarmCombat:SomeFutureMissing",
          problems(swarm=SWARM+'\\nlocal missed=require(script.Parent:WaitForChild("SomeFutureMissing"))'))
    def test_client_script_must_not_be_server_script(self):
        p=json.loads(PROJECT)
        p["tree"]["ServerScriptService"]["ClientWrong"]={"$path":"EGGRUMBLE_CombatFeel.client.luau"}
        self.assertIn("no unauthorized client script in ServerScriptService",problems(project=json.dumps(p)))
    def test_no_fake_author_server_ko(self):
        self.assertIn("original neutral real KO feedback",problems(swarm=SWARM.replace("ImpactFeedback.ko(","-- FakeKo(")))
    def test_author_impact_not_shadowed(self):
        self.assertIn("original server actual hit feedback",problems(role=ROLE.replace("ImpactFeedback.attacker(","-- silent(")))
    def test_no_separate_item_host(self):
        p=json.loads(PROJECT)
        p["tree"]["ServerScriptService"]["EGGRUMBLE_FieldItemPreview"]={"$path":"EGGRUMBLE_FieldItemPreview.server.luau"}
        self.assertIn("single authentic V3 host",problems(project=json.dumps(p)))
if __name__=="__main__":unittest.main()
