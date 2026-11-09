"""R3 offline Lua 5.4 mocks via optional lupa; never controls Studio.

Run from repository root with lupa on PYTHONPATH. The git-show pipe adapter
replaces POSIX /dev/null redirection on Windows, preserving immutable fixtures.
"""
from pathlib import Path
import re
import subprocess
import sys

from lupa.lua54 import LuaRuntime


def run():
    specs = [Path("tests/auto/studio_preview_hud_replication_spec.lua"),
             Path("tests/auto/studio_unsaved_preview_spec.lua")]
    specs += sorted(Path("tests/auto").glob("progression*_spec.lua"))
    failed = 0
    for spec in specs:
        lua = LuaRuntime(unpack_returned_tuples=True)

        def git_pipe(command, mode="r"):
            match = re.fullmatch(r"git show ([0-9a-f]{40}):([\w/.-]+)(?: 2>/dev/null)?", command)
            if not match or mode != "r":
                raise ValueError("unsupported pipe: " + command)
            result = subprocess.run(["git", "show", f"{match[1]}:{match[2]}"],
                                    capture_output=True, encoding="utf-8")
            pipe = lua.table()
            pipe.read = lambda *_: result.stdout
            pipe.close = lambda *_: result.returncode == 0
            return pipe

        lua.globals().io.popen = git_pipe
        lua.execute('os.exit=function(code) error("test exit "..tostring(code)) end')
        try:
            lua.execute(spec.read_text(encoding="utf-8"))
            print("SPEC_PASS", spec, flush=True)
        except Exception as error:
            failed += 1
            print("SPEC_FAIL", spec, str(error), flush=True)
    print(f"R3_LUA_FILES {len(specs)-failed} passed / {failed} failed", flush=True)
    return bool(failed)


if __name__ == "__main__":
    sys.exit(run())
