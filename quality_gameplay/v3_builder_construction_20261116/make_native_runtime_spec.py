#!/usr/bin/env python3
"""Native-only deterministic wrapper of the ACTUAL builder module source.

Native Luau require isolates globals, so the Roblox-service fake environment
in runtime.spec.luau is not inherited by a separately required file.
Source injection is exactly the module bytes, without hand-copied logic.
This does not replace Roblox Studio tests or bind any Game Remote.
"""
from pathlib import Path
HERE=Path(__file__).resolve().parent
original=(HERE/"EGGRUMBLE_BuilderConstruction.luau").read_text(encoding="utf-8")
template=(HERE/"EGGRUMBLE_BuilderConstruction.runtime.spec.luau").read_text(encoding="utf-8")
needle='local Build=require("./EGGRUMBLE_BuilderConstruction")'
assert template.count(needle)==1,"single original module injection anchor required"
assert original.startswith("--!strict\n"),"must inject original strict Luau source"
assert original.rstrip().endswith("return Build"),"module must return one Builder API"
assert "function Build.place(" in original and "function Build.clear(" in original
generated=template.replace(needle,"local Build=(function()\n"+original+"\nend)()")
target=HERE/"EGGRUMBLE_BuilderConstruction.runtime.generated.luau"
target.write_text(generated,encoding="utf-8")
assert generated.count(original)==1,"actual source exact once"
print("GQ_BUILDER_NATIVE_RUNTIME_SAME_SOURCE_INJECTION_PASS",len(original.encode("utf-8")),target)
