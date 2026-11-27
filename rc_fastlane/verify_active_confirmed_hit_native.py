"""Exercise the active hit cue with the authenticated author fixtures."""

import argparse
import ast
import json
from pathlib import Path

from apply_active_confirmed_hit import GAME, HUD, PACKAGE
from apply_core_round_ready import once
from integrate import gitblob
from test_p0_ready_composed_native import unique_function


EXTRA_SERVER = r'''
setup()
for _,seq in ipairs({0, -1, .5, 1/0, math.sqrt(-1), "1", 1000000001}) do
    invoke(seq)
end
assert(#remote.sent==0 and lastSeq[env.player]==nil,"INVALID_SEQUENCE_CONSUMED")

setup()
map.teams.BLUE.core.Position=V(6,0,0)
match.hp.BLUE=1
invoke()
assert(#remote.sent==1 and remote.sent[1].status=="HIT" and remote.sent[1].target=="CASTLE")
assert(env.stopped==1 and match.hp.BLUE==0,"CASTLE_BREAK_WAS_NOT_RULES_WIN")

setup()
EXPERIMENTAL_FIVE_EGG_MODE=true
env.bot={hum={Health=100,TakeDamage=function(h) h.Health=0 end}}
invoke()
assert(#remote.sent==1 and remote.sent[1].status=="MISS" and env.bot.hum.Health==100,
       "FIVE_EGG_MUST_NOT_TOUCH_SOLO_BOT")
print("ACTIVE_FB019_REAL_SEQUENCE_CASTLE_WIN_AND_MODE_NEGATIVES_PASS")
'''

EXTRA_HUD = r'''
local baseText=attack.Text
ack("HIT",math.sqrt(-1))
ack("HIT",1/0)
ack("HIT",1000000001)
ack("HIT",4.5)
ack("INVALID",99)
assert(#queue==0 and attack.Text==baseText,"UNRECOGNIZED_PACKET_CONSUMED")
ack("HIT",4)
local hitText=attack.Text
assert(#queue==1 and hitText~=baseText,"INVALID_PACKET_RETIRED_VALID_RESULT")
ack("MISS",5)
local missText=attack.Text
assert(#queue==2 and missText~=baseText and missText~=hitText)
queue[1]()
assert(attack.Text==missText,"EARLIER_FLASH_RESET_NEWER")
queue[2]()
assert(attack.Text==baseText)
print("ACTIVE_FB019_HUD_BAD_PACKET_AND_EARLY_RESET_NEGATIVES_PASS")
'''


def segment(text, start, end):
    assert text.count(start) == text.count(end) == 1, (start, end)
    a = text.index(start)
    return text[a:text.index(end, a)]


def program(dist, previous):
    lock = json.loads((PACKAGE / "source_lock.json").read_bytes())
    raw = (PACKAGE / "original_native.py").read_bytes()
    assert gitblob(raw) == lock["source_origins"]["native_blob"]
    tags = {"PREFIX", "SERVER_TESTS", "HUD_SETUP", "HUD_TESTS"}
    constants = {target.id: ast.literal_eval(node.value) for node in ast.parse(raw).body
                 if isinstance(node, ast.Assign) for target in node.targets
                 if isinstance(target, ast.Name) and target.id in tags}
    assert set(constants) == tags
    game = (dist / "src" / GAME).read_text("utf-8")
    old_game = previous.read_text("utf-8")
    hud = (dist / "src" / HUD).read_text("utf-8")
    snapshot = "snapshotFor = function(player: Player)"
    assert unique_function(game, snapshot) == unique_function(old_game, snapshot)
    marker, after = "local function applyAttack(player: Player, data)", "-- H1 RAIDER wind:"
    attack = segment(game, marker, after)
    assert "remote:FireClient(player,snapshotFor(player))" not in attack
    cue = segment(hud, "local originalAttackText = attack.Text", "trapButton.MouseButton1Click:Connect")

    rules = (dist / "src/server/S1Rules.luau").read_text("utf-8")
    prefix = constants["PREFIX"]
    mock = segment(prefix, "    Rules={\n", "    RunService={IsStudio=")
    prefix = once(prefix, mock, "    Rules=ExactRules\n")
    prefix = "local ExactRules=(function()\n" + rules + "\nend)()\n" + prefix
    cases = once(constants["SERVER_TESTS"],
                 '    assert(snapshots==(if env.mobHits>0 then 1 else 0),"V2_REAL_HIT_SNAPSHOT_MISSING")',
                 '    assert(snapshots==0,"EXISTING_SNAPSHOT_CADENCE_CHANGED")')
    return "\n".join((prefix, attack, cases, EXTRA_SERVER, constants["HUD_SETUP"], cue,
                      constants["HUD_TESTS"], EXTRA_HUD))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--before-game", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_bytes(program(args.dist, args.before_game).encode("utf-8"))
