"""Studio MCP Windows launcher startup must use the native Roblox working dir.
No Windows batch execution, network, GUI, privileged review, or Studio connection.
"""
from __future__ import annotations
import pathlib
import subprocess
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import studio_mcp_readonly_probe as m

class WindowsMcpCwdContract(unittest.TestCase):
    def invoke(self, raw="/temporary/user space/Roblox/mcp.bat"):
        return m._mcp_popen_spec(pathlib.Path(raw))

    def test_starts_exact_official_batch_path(self):
        args, kw=self.invoke()
        self.assertEqual(args,["cmd.exe","/c","/temporary/user space/Roblox/mcp.bat"])

    def test_child_process_cwd_is_roblox_folder(self):
        args,kw=self.invoke()
        self.assertEqual(kw["cwd"],"/temporary/user space/Roblox")

    def test_cwd_matches_actual_launcher_parent(self):
        for raw in ("/a/Roblox/mcp.bat","/a b/c d/Roblox/mcp.bat","/opt/x/roblox/MCP.BAT"):
            with self.subTest(raw=raw):
                args,kw=self.invoke(raw)
                self.assertEqual(pathlib.Path(kw["cwd"]),pathlib.Path(raw).parent)

    def test_never_launches_through_shell_flag(self):
        _,kw=self.invoke()
        self.assertIs(kw["shell"],False)

    def test_does_not_interpolate_shell_commands(self):
        args,kw=self.invoke()
        self.assertEqual(len(args),3)
        self.assertEqual(args[:2],["cmd.exe","/c"])
        self.assertNotIn("&&",args[-1])
        self.assertNotIn("cd /d",args[-1])

    def test_path_with_spaces_retained_as_single_arg(self):
        args,kw=self.invoke("/temporary/my user/App Data/Roblox/mcp.bat")
        self.assertEqual(args[2],"/temporary/my user/App Data/Roblox/mcp.bat")
        self.assertEqual(kw["cwd"],"/temporary/my user/App Data/Roblox")

    def test_stdin_stays_piped_for_stdio_mcp(self):
        _,kw=self.invoke()
        self.assertEqual(kw["stdin"],subprocess.PIPE)

    def test_stdout_stays_piped_for_stdio_mcp(self):
        _,kw=self.invoke()
        self.assertEqual(kw["stdout"],subprocess.PIPE)

    def test_stderr_is_suppressed_not_logged(self):
        _,kw=self.invoke()
        self.assertEqual(kw["stderr"],subprocess.DEVNULL)

    def test_utf8_text_stream_retained(self):
        _,kw=self.invoke()
        self.assertEqual(kw["encoding"],"utf-8")
        self.assertIs(kw["text"],True)
        self.assertEqual(kw["bufsize"],1)

    def test_reject_wrong_batch_name(self):
        with self.assertRaises(m.ProbeError):
            self.invoke("/tmp/Roblox/mcp-fake.bat")

    def test_reject_other_parent_folder(self):
        with self.assertRaises(m.ProbeError):
            self.invoke("/tmp/Untrusted/mcp.bat")

    def test_reject_non_path_launcher(self):
        with self.assertRaises(m.ProbeError):
            m._mcp_popen_spec("/tmp/Roblox/mcp.bat")

    def test_no_ambient_environment_dump(self):
        _,kw=self.invoke()
        self.assertNotIn("env",kw)
        self.assertNotIn("capture_output",kw)

    def test_popen_options_not_controlled_by_caller(self):
        args,kw=self.invoke()
        self.assertEqual(set(kw),{"cwd","shell","stdin","stdout","stderr","text","encoding","bufsize"})


if __name__=="__main__":
    unittest.main()
