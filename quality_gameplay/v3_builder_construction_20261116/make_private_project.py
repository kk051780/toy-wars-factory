#!/usr/bin/env python3
"""Create a private 23-source Roblox project from untouched #482 21-source manifest."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ORIGINAL=ROOT/"handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
original=json.loads((ORIGINAL/"EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8"))
tracked=[]
def adapt(node):
    if isinstance(node,dict):
        if "$path" in node:
            old=node["$path"]
            assert "/" not in old and ".." not in old,old
            full=ORIGINAL/old
            assert full.is_file(),str(full)
            tracked.append((old,full))
            return {"$path":"../../handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/"+old}
        return {k:adapt(v) for k,v in node.items()}
    return node
tree=adapt(original["tree"])
assert len(tracked)==21,len(tracked)
assert len(set(name for name,_ in tracked))==21
server=tree["ServerScriptService"]
for name in ["EGGRUMBLE_BuilderConstruction","EGGRUMBLE_BuilderPlacementPolicy"]:
    assert name not in server
    source=HERE/(name+".luau")
    assert source.is_file(),source
    server[name]={"$path":source.name}
project={"name":"EGGRUMBLE_BUILDER_PRIVATE_23_SOURCE_NOT_OFFICIAL_RC","tree":tree}
out=HERE/"EGGRUMBLE_BUILDER_PRIVATE.project.json"
out.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert sum(1 for _ in tracked)+2==23
print("BUILDER_PRIVATE_PROJECT_23_OF_23_READY",out)
