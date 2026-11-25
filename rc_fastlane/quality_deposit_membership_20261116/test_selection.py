"""GQ586 isolated actual Host callback selection negative/mutation tests."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_deposit import START, END, OLD, NEW, FLAG, overlay, body, flatten, prepare, HOST

HOST_SOURCE = (
    'local sessions={}\n'
    'local joined={}\n'
    + START +
    OLD +
    '  local c=session.rules.castles[entry.id]\n'
    '  if c.alive and c.heldEggs>0 then\n'
    '   local ok=pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end)\n'
    '   if ok then session.refresh() end\n'
    '  end\n'
    + END + '\n'
    'local function other() return true end\n'
)

class GQ586(unittest.TestCase):
    def test_single_callback_only_and_rollback(self):
        result = overlay(HOST_SOURCE)
        self.assertEqual(result.count(FLAG), 1)
        self.assertEqual(result.replace(NEW, OLD, 1), HOST_SOURCE)
        self.assertEqual(result.count("Rules.depositEggs("), 1)
        self.assertEqual(result.count("session.refresh()"), 1)
    def test_guard_blocks_both_member_and_session_mismatch(self):
        result = overlay(HOST_SOURCE)
        callback = body(result)
        self.assertIn("joined[p.UserId]~=session.mode", callback)
        self.assertIn("sessions[session.mode]~=session", callback)
        self.assertLess(callback.index("joined[p.UserId]"), callback.index("Rules.depositEggs("))
    def test_rejects_duplicate(self):
        with self.assertRaisesRegex(ValueError, "ALREADY_SELECTED"):
            overlay(overlay(HOST_SOURCE))
    def test_rejects_original_callback_mutation(self):
        with self.assertRaisesRegex(ValueError, "OLD_CALLBACK_ALREADY_MODIFIED"):
            overlay(HOST_SOURCE.replace(OLD, OLD.replace("entry.id", "entry.Id")))
    def test_rejects_wrong_prompt(self):
        with self.assertRaisesRegex(ValueError, "CALLBACK_ANCHOR_DRIFT"):
            overlay(HOST_SOURCE.replace("OwnEggDeposit", "OwnEggDepositX").replace(
                'prompt(deposit,"卵を納入"', 'prompt(deposit,"納入"'))
    def test_rejects_missing_refresh(self):
        with self.assertRaisesRegex(ValueError, "REFRESH_LOST"):
            overlay(HOST_SOURCE.replace("if ok then session.refresh() end", "if ok then return end"))
    def test_rejects_second_deposit_callback(self):
        with self.assertRaisesRegex(ValueError, "CALLBACK_ANCHOR_DRIFT"):
            overlay(HOST_SOURCE + START + OLD + END)
    def test_rejects_already_partially_guarded(self):
        with self.assertRaisesRegex(ValueError, "ALREADY_MODIFIED"):
            overlay(HOST_SOURCE.replace(OLD, '  if joined[p.UserId]~=session.mode then return end\n' + OLD))
    def test_single_runtime_owner_31(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); mapping={"ServerScriptService":{}}
            for i in range(30):
                name="M%02d"%i
                (root/(name+".luau")).write_text("return {}\n")
                mapping["ServerScriptService"][name]={"$path":name+".luau"}
            name=HOST[-1]
            (root/(name+".server.luau")).write_text(HOST_SOURCE)
            mapping["ServerScriptService"][name]={"$path":name+".server.luau"}
            base=root/"base.json";out=root/"selected.json"
            base.write_text(json.dumps({"tree":mapping}))
            prepare(base,out)
            _,old=flatten(base);_,new=flatten(out)
            self.assertEqual(sum(old[k].read_bytes()!=new[k].read_bytes() for k in old),1)
            self.assertEqual(new[HOST].read_text().replace(NEW,OLD),HOST_SOURCE)
            self.assertTrue(json.loads((root/"GQ586_SOURCE_RECEIPT.json").read_text())["other_30_byte_exact"])
    def test_rejects_noncanonical_31(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"empty.json";p.write_text(json.dumps({"tree":{"ServerScriptService":{}}}))
            with self.assertRaisesRegex(ValueError,"NOT_SINGLE_HOST_31"):
                flatten(p)

if __name__ == "__main__":
    unittest.main()
