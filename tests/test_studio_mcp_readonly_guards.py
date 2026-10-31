"""Official Studio MCP read-only probe; all cases fake transport, NEVER engine."""
from pathlib import Path
import contextlib, io, queue, sys, unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import studio_mcp_readonly_probe as mod

class Fake:
    def __init__(self,protocol=None,tools=None,result=None):
        self.protocol=mod.PROTOCOL_VERSION if protocol is None else protocol
        self.tools=tools if tools is not None else [{"name":"list_roblox_studios"},{"name":"multi_edit"},{"name":"start_stop_play"},{"name":"execute_luau"}]
        self.result=result if result is not None else {"content":[{"type":"text","text":"[]"}]}
        self.calls=[]
    def request(self,method,params):
        self.calls.append((method,params))
        if method=="initialize":return {"protocolVersion":self.protocol}
        if method=="tools/list":return {"tools":self.tools}
        if method=="tools/call":
            assert params=={"name":"list_roblox_studios","arguments":{}}
            return self.result
        raise AssertionError("unreviewed RPC method")
    def notify(self,method,params):
        self.calls.append((method,params))
        assert method=="notifications/initialized" and params=={}

class FakeQ:
    def __init__(self,items):self.items=list(items);self.timeouts=[]
    def get(self,timeout):
        self.timeouts.append(timeout)
        if not self.items:raise queue.Empty
        return self.items.pop(0)

class ProbeGuards(unittest.TestCase):
    def test_default_never_spawns(self):
        stdout=io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(mod.main([]),0)
        self.assertIn("NOT_RUN_DEFAULT",stdout.getvalue())

    def test_offline_read_only_success_untrusted(self):
        obj=Fake()
        res=mod.probe(obj)
        self.assertEqual([x[0] for x in obj.calls],
                         ["initialize","notifications/initialized","tools/list","tools/call"])
        self.assertFalse(res["studio_session_authenticated"])
        self.assertFalse(res["studio_engine_verified"])
        self.assertFalse(res["play_started"])
        self.assertFalse(res["scripts_modified"])
        self.assertFalse(res["external_publish"])
        self.assertIsNone(res["connected_studio_count_unverified"])

    def test_no_mutation_tool_invoked(self):
        obj=Fake()
        mod.probe(obj)
        self.assertEqual(obj.calls[-1][1],{"name":"list_roblox_studios","arguments":{}})
        self.assertEqual(mod.ALLOWED_TOOLS,frozenset({"list_roblox_studios"}))

    def test_unknown_future_protocol_refused(self):
        with self.assertRaises(mod.ProbeError):mod.probe(Fake(protocol="2099-01-01"))

    def test_invalid_calendar_protocol_refused(self):
        with self.assertRaises(mod.ProbeError):mod.probe(Fake(protocol="2025-99-99"))

    def test_missing_listing_tool_refused(self):
        with self.assertRaises(mod.ProbeError):mod.probe(Fake(tools=[]))

    def test_duplicate_listing_tool_refused(self):
        with self.assertRaises(mod.ProbeError):
            mod.probe(Fake(tools=[{"name":"list_roblox_studios"}]*2))

    def test_oversize_listing_refused(self):
        with self.assertRaises(mod.ProbeError):
            mod.probe(Fake(tools=[{"name":"list_roblox_studios"}]*1024))

    def test_server_error_refused(self):
        with self.assertRaises(mod.ProbeError):
            mod.probe(Fake(result={"isError":True,"content":[]}))

    def test_integer_error_refused(self):
        with self.assertRaises(mod.ProbeError):
            mod.probe(Fake(result={"isError":1,"content":[]}))

    def test_nontext_content_refused(self):
        with self.assertRaises(mod.ProbeError):
            mod.probe(Fake(result={"content":[{"type":"image","data":"x"}]}))

    def test_oversize_content_refused(self):
        with self.assertRaises(mod.ProbeError):
            mod.probe(Fake(result={"content":[{"type":"text","text":"x"*1000000}]}))

    def test_studio_id_never_authenticated_by_fake_data(self):
        res=mod.probe(Fake(result={"content":[{"type":"text","text":'[{"studio_id":"fake","name":"TOY WARS"}]'}]}))
        self.assertIsNone(res["connected_studio_count_unverified"])

    def test_denied_methods_before_any_send(self):
        t=object.__new__(mod.JsonLineTransport)
        with self.assertRaises(mod.ProbeError):t.request("scripts/edit",{})

    def test_denied_tool_calls_before_any_send(self):
        t=object.__new__(mod.JsonLineTransport)
        with self.assertRaises(mod.ProbeError):
            t.request("tools/call",{"name":"execute_luau","arguments":{}})
        with self.assertRaises(mod.ProbeError):
            t.request("tools/call",{"name":"list_roblox_studios","arguments":{"id":"bad"}})

    def test_reject_list_pagination_before_send(self):
        t=object.__new__(mod.JsonLineTransport)
        with self.assertRaises(mod.ProbeError):t.request("tools/list",{"cursor":"next"})

    def test_reject_untrusted_notification(self):
        t=object.__new__(mod.JsonLineTransport)
        with self.assertRaises(mod.ProbeError):t.notify("notifications/cancelled",{})

    def test_nonfinite_json_rejected(self):
        with self.assertRaises(mod.ProbeError):mod._strict_json_constant("NaN")

    def test_json_duplicate_keys_rejected(self):
        with self.assertRaises(mod.ProbeError):mod._json_unique([("id",1),("id",2)])

    def test_windows_cmd_metacharacters_rejected(self):
        for v in [r"C:\Users\A&B\AppData\Local",r"C:\Users\X%TEMP%\AppData\Local",
                  r"C:\Users\A!B\AppData\Local",r"\\server\share\AppData\Local"]:
            with self.subTest(v=v):
                with self.assertRaises(mod.ProbeError):mod.validate_localappdata(v)

    def test_windows_path_with_space_can_pass_lexical_check(self):
        self.assertEqual(mod.validate_localappdata(r"C:\Users\Test User\AppData\Local"),
                         r"C:\Users\Test User\AppData\Local")

    def test_bounded_global_request_deadline(self):
        t=object.__new__(mod.JsonLineTransport)
        t.sequence=0
        t.q=FakeQ(['{"jsonrpc":"2.0","method":"notifications/progress"}\n']*3+
                  ['{"jsonrpc":"2.0","id":1,"result":{}}\n'])
        t._send=lambda x:None
        clock=iter([100.,104.,108.,112.,116.])
        with mock.patch.object(mod.time,"monotonic",lambda:next(clock)):
            with self.assertRaises(mod.ProbeError):t.request("tools/list",{})
        self.assertTrue(all(0 < x <= mod.TIMEOUT for x in t.q.timeouts))

    def test_bool_response_id_is_denied(self):
        t=object.__new__(mod.JsonLineTransport)
        t.sequence=0;t.q=FakeQ(['{"jsonrpc":"2.0","id":true,"result":{}}\n'])
        t._send=lambda x:None
        with self.assertRaises(mod.ProbeError):t.request("tools/list",{})

if __name__=="__main__":unittest.main()
