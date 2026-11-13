"""Static source boundary + independent Python reference oracle only.
NOT native Luau execution or actual Roblox Studio evidence.
"""
from pathlib import Path
import json, re, unittest
R=Path(__file__).resolve().parents[1]
RULES=(R/"src/RumbleLinkCueRules.luau").read_text()
PREVIEW=(R/"demo/RumbleLinkPreview.client.luau").read_text()
WORDS={"SCOUT_ASSIST":"みつけた！","SEA_ESCORT":"うみルート！",
       "TRAP_GUARD":"ナイスガード！","CASTLE_RECAPTURE":"とりかえした！"}

def accept(s,p,now,team):
    if not isinstance(s,dict) or not isinstance(p,dict): return None
    if team not in ("RED","BLUE") or p.get("team")!=team: return None
    rid=p.get("roundId"); seq=p.get("seq"); exp=p.get("expiresAt")
    if not isinstance(rid,str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",rid): return None
    if type(seq) is not int or seq<1 or seq>1000000000: return None
    if p.get("kind") not in WORDS or type(exp) not in (int,float): return None
    if not isinstance(now,(int,float)) or exp<now or exp>now+4: return None
    if s.get("roundId")!=rid: s.update(roundId=rid,lastSeq=0,nextAllowed=0)
    if seq<=s["lastSeq"]: return None
    s["lastSeq"]=seq
    if now<s["nextAllowed"]: return None
    s["nextAllowed"]=now+2.2
    return WORDS[p["kind"]]

class Contract(unittest.TestCase):
    def setUp(self):
        self.s={"roundId":None,"lastSeq":0,"nextAllowed":0}
        self.p={"roundId":"Round_1","seq":1,"kind":"SCOUT_ASSIST",
                "team":"BLUE","expiresAt":11.5}
    def test_four_distinct_cues(self):
        for i,k in enumerate(WORDS):
            p=dict(self.p,seq=i+1,kind=k,expiresAt=12+i*3)
            self.assertEqual(accept(self.s,p,10+i*3,"BLUE"),WORDS[k])
    def test_reject_enemy_team(self): self.assertIsNone(accept(self.s,self.p,10,"RED"))
    def test_reject_stale(self): self.assertIsNone(accept(self.s,dict(self.p,expiresAt=9),10,"BLUE"))
    def test_reject_far_future(self): self.assertIsNone(accept(self.s,dict(self.p,expiresAt=20),10,"BLUE"))
    def test_reject_unknown(self): self.assertIsNone(accept(self.s,dict(self.p,kind="PAID_SKILL"),10,"BLUE"))
    def test_reject_invalid_id(self): self.assertIsNone(accept(self.s,dict(self.p,roundId="x\nTOKEN"),10,"BLUE"))
    def test_reject_seq_bool(self): self.assertIsNone(accept(self.s,dict(self.p,seq=True),10,"BLUE"))
    def test_reject_nil(self): self.assertIsNone(accept(None,self.p,10,"BLUE"))
    def test_replay_prevention(self):
        self.assertIsNotNone(accept(self.s,self.p,10,"BLUE"))
        self.assertIsNone(accept(self.s,self.p,13,"BLUE"))
    def test_sequence_regression(self):
        self.assertIsNotNone(accept(self.s,dict(self.p,seq=4),10,"BLUE"))
        self.assertIsNone(accept(self.s,dict(self.p,seq=3,expiresAt=13.5),12,"BLUE"))
    def test_display_throttle(self):
        self.assertIsNotNone(accept(self.s,self.p,10,"BLUE"))
        self.assertIsNone(accept(self.s,dict(self.p,seq=2),11,"BLUE"))
        self.assertIsNotNone(accept(self.s,dict(self.p,seq=3,expiresAt=13.5),12.3,"BLUE"))
    def test_new_round_reset(self):
        self.assertIsNotNone(accept(self.s,self.p,10,"BLUE"))
        self.assertIsNotNone(accept(self.s,dict(self.p,roundId="Round_2",expiresAt=12),11,"BLUE"))
    def test_production_no_authority_source(self):
        for bad in ("FireServer","OnServerEvent","UpdateAsync","SetAsync","GetAsync",
                    "MarketplaceService","DataStoreService","TakeDamage","FireClient"):
            self.assertNotIn(bad,RULES)
    def test_preview_synthetic_not_game_remote(self):
        self.assertIn('if not RunService:IsStudio() then return end',PREVIEW)
        for bad in ("FireServer","OnServerEvent","MarketplaceService","DataStoreService"):
            self.assertNotIn(bad,PREVIEW)
    def test_source_covers_cue_kinds(self):
        for kind,word in WORDS.items():
            self.assertIn(kind,RULES); self.assertIn(word,RULES)
    def test_rojo_preview_only(self):
        tree=json.loads((R/"default.project.json").read_text())["tree"]
        self.assertIn("RumbleLinkCueRules",tree["ReplicatedStorage"])
        self.assertIn("RumbleLinkPreview",tree["StarterPlayer"]["StarterPlayerScripts"])
        self.assertNotIn("ServerScriptService",tree)
    def test_no_game_authority_paths(self):
        for path in R.rglob("*.luau"):
            self.assertNotIn("Game.server",path.name)
            self.assertNotIn("PersistentHatch",path.name)

if __name__=="__main__": unittest.main()
