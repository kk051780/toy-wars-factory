#!/usr/bin/env python3
"""Verify the actual original owner files against immutable source refs.
This is STATIC owner source QA. Never implies a Studio/RC integration.
"""
import hashlib
from pathlib import Path
sources = {
    "v7_horde": ("_v7/handoffs/P0D-MUSOU-CHAOS-H1-20261113-01/inputs/MusouHorde.luau",
                 "fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"),
    "v7_game": ("_v7/handoffs/P0D-MUSOU-CHAOS-H1-20261113-01/inputs/Game.server.luau",
                "5979be7d70a415a8e954ff6a04babf4e3e09fd87"),
    "b42_game": ("_b42/handoffs/P0D-FIRST90-GUIDED-H1-20261113-01/inputs/Game.server.luau",
                 "21b866e801a53ba7ebd66132ae55fe28608750d6"),
}
text = {}
for key,(path,sha) in sources.items():
    data = Path(path).read_bytes()
    blob = hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    assert blob==sha, (key,blob,sha)
    text[key] = data.decode("utf-8")
v7=text["v7_horde"]; game=text["v7_game"]; first=text["b42_game"]
checks=[
  ("one elite created", "local elite=(i==MAX_ACTIVE)" in v7),
  ("elite truth field", "elite=elite,deadUntil=0" in v7),
  ("real KO HP transition", "m.hp=math.max(0,beforeHp-dealt)" in v7),
  ("server KO deadUntil", "m.deadUntil=now+8" in v7),
  ("single server NPC hit function", v7.count("function Horde:hit(")==1),
  ("typed count lacks elite KO receipt", "return touched,defeated" in v7),
  ("single v7 PvE callsite", game.count("horde:hit(")==1),
  ("two b42 PvE callsites", first.count("horde:hit(")==2),
  ("v7 Game remains one server", "local horde=MusouHorde.new(map.model)" in game),
  ("b42 Game remains one server", "local horde=MusouHorde.new(map.model)" in first),
  ("studio gate v7 present", "if RunService:IsStudio() then" in game),
  ("studio gate b42 present", "if RunService:IsStudio() then" in first),
]
for label,ok in checks:
    assert ok, "UPSTREAM_SOURCE_CONTRACT_DRIFT: "+label
print("UPSTREAM_OWNER_ACTUAL_SOURCE_LOCK_3_OF_3_AND_12_CONTRACT_CHECKS_PASS")
