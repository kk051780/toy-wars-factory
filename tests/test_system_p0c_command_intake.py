"""P0-C adversarial offline tests; parsing never implies PC authorization."""
import json
import unittest
from datetime import datetime, timezone
from tools.system_p0c_command_intake import inspect_untrusted_intent

NOW = datetime(2026,11,8,6,41,tzinfo=timezone.utc)
HOST = "DESKTOP-EASS441"

def sample():
    return {"schema":1, "repo":"kk051780/toy-wars-factory",
            "issuer_claim":"kk051780",
            "source_kind":"CHATGPT_GITHUB_INTENT_UNTRUSTED",
            "action":"PING_STATUS_READONLY",
            "work_id":"P0C_READONLY_HANDSHAKE_20261108_A",
            "nonce":"0123456789abcdef0123456789abcdef",
            "host_id":HOST, "target_branch":"main",
            "main_sha":"e5deff4d5681bca4823a3da0f848e01bc089ae6e",
            "issued_at":"2026-11-08T06:40:00Z",
            "expires_at":"2026-11-08T06:45:00Z"}

def evaluate(d=None,**kwargs):
    return inspect_untrusted_intent(json.dumps(sample() if d is None else d),
                                    now_utc=NOW,expected_host=HOST,**kwargs)

class P0CIntakeTests(unittest.TestCase):
    def assertDenied(self, r):
        for k in ("provider_authenticated","owner_authorized","host_authorized",
                  "codex_execution_authorized","may_run_commands"):
            self.assertIs(r[k],False)
    def mutate(self,key,value):
        d=sample(); d[key]=value
        r=evaluate(d); self.assertFalse(r["read_only_intent_valid"]);self.assertDenied(r)
    def test_valid_diagnostic_never_authorizes(self):
        r=evaluate();self.assertTrue(r["read_only_intent_valid"]);self.assertDenied(r)
    def test_claimed_owner_still_untrusted(self):
        self.assertEqual(evaluate()["status"],"READ_ONLY_INTENT_VALID_BUT_UNTRUSTED")
    def test_wrong_owner(self): self.mutate("issuer_claim","not-owner")
    def test_wrong_repo(self): self.mutate("repo","attacker/repo")
    def test_wrong_source(self): self.mutate("source_kind","TRUSTED")
    def test_wrong_host(self): self.mutate("host_id","OTHER-PC")
    def test_wrong_branch(self): self.mutate("target_branch","refs/heads/main")
    def test_unpinned_sha(self): self.mutate("main_sha","main")
    def test_bad_nonce(self): self.mutate("nonce","123")
    def test_bad_work_id(self): self.mutate("work_id","DO_ANYTHING")
    def test_extra_prompt(self): self.mutate("prompt","powershell -Command ...")
    def test_lua_action(self): self.mutate("action","RUN_LUA")
    def test_publish_action(self): self.mutate("action","ROBLOX_PUBLISH")
    def test_codex_autostart(self): self.mutate("action","CODEX_AUTOSTART")
    def test_missing_field(self):
        d=sample();d.pop("nonce")
        self.assertFalse(evaluate(d)["read_only_intent_valid"])
    def test_duplicate_json_keys(self):
        j=json.dumps(sample()).replace('"schema": 1','"schema": 1, "schema": 1')
        r=inspect_untrusted_intent(j,now_utc=NOW,expected_host=HOST)
        self.assertFalse(r["read_only_intent_valid"]);self.assertDenied(r)
    def test_expired(self): self.mutate("expires_at","2026-11-08T06:40:30Z")
    def test_future(self): self.mutate("issued_at","2026-11-08T06:42:00Z")
    def test_excessive_ttl(self): self.mutate("expires_at","2026-11-08T07:40:00Z")
    def test_replay(self):
        r=evaluate(seen_work_ids={sample()["work_id"]})
        self.assertFalse(r["read_only_intent_valid"]);self.assertDenied(r)
    def test_bad_schema_boolean(self): self.mutate("schema",True)
    def test_bad_utf8(self):
        r=inspect_untrusted_intent(b"\xff",now_utc=NOW,expected_host=HOST)
        self.assertFalse(r["read_only_intent_valid"])
    def test_oversized(self):
        r=inspect_untrusted_intent(b"x"*2049,now_utc=NOW,expected_host=HOST)
        self.assertFalse(r["read_only_intent_valid"])
    def test_naive_clock(self):
        r=inspect_untrusted_intent(json.dumps(sample()),now_utc=datetime(2026,11,8),expected_host=HOST)
        self.assertFalse(r["read_only_intent_valid"])
    def test_nonobject(self):
        r=inspect_untrusted_intent("[]",now_utc=NOW,expected_host=HOST)
        self.assertFalse(r["read_only_intent_valid"])

if __name__=="__main__": unittest.main()
