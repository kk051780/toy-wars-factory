#!/usr/bin/env python3
"""Fail closed on cosmetics-only three-realm Studio asset, not real avatar physics."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def require(ok,msg):
 if not ok:raise ValueError(msg)
def blob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
def check_source():
 m=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf8"))
 require(m["schema"]=="P0D_WORLD_G7_THREE_REALMS_SOURCE_SHA1_LOCK_V1","schema")
 require(m["scope"]=="S2_PLUS_SOURCE_ONLY_STUDIO_SHOWROOM_NOT_H1","wrong scope")
 require(m["cards"]==["WF-13","WF-14","WF-15"],"field ids")
 require(len(m["source_files"])==5,"manifest size")
 seen=set()
 for item in m["source_files"]:
  p=item["path"]
  require(p not in seen and ".." not in Path(p).parts and not p.startswith("/"),"unsafe path")
  raw=(ROOT/p).read_bytes()
  require(item["sha"]==blob(raw) and item["bytes"]==len(raw),"file changed "+p)
  seen.add(p)
 require(seen=={"src/RiftDirector.luau","src/FieldShowcase.server.luau","default.project.json","README.md","FIELD_CARDS.md"},"unsafe files")
 return True
def check_contract(world=None,director=None,project=None,cards=None):
 world=world if world is not None else (ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8")
 director=director if director is not None else (ROOT/"src/RiftDirector.luau").read_text(encoding="utf8")
 cards=cards if cards is not None else (ROOT/"FIELD_CARDS.md").read_text(encoding="utf8")
 project=project if project is not None else json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
 for x in ('if not RunService:IsStudio() then return end','G7_FANTASY_REALM_SOURCE_PREVIEW','G7_FREE_HUB',
           'G7_SPACE_PERMANENT_BRIDGE','G7_HEAVEN_PERMANENT_BRIDGE','G7_ABYSS_PERMANENT_BRIDGE',
           'Director.state','local spawn=Instance.new("SpawnLocation")','p.CanCollide=solid==true','status.Text',
           'areaInfo.beacon.Transparency','G7_SPACE_STAR_','G7_HEAVEN_CLOUD_','G7_ABYSS_OBSIDIAN_SPIRE_'):
  require(x in world,"world contract missing "+x)
 for x in ('D.CYCLE_SECONDS=95','D.WAIT_SECONDS=20','D.ANNOUNCE_SECONDS=5',
           'D.ACTIVE_SECONDS=25','D.COOLDOWN_SECONDS=45','"SPACE","HEAVEN","ABYSS"',
           'world_access_is_free=true','permanent_ground_route_open=true','server_gameplay_bonus=false',
           'function D.state(elapsed,seed)','function D.isSymmetric','function D.safeForCarrier'):
  require(x in director,"director contract missing "+x)
 for forbidden in ('RemoteEvent','DataStoreService','MarketplaceService','FireServer(',
                   'Humanoid:TakeDamage','Humanoid.WalkSpeed','Workspace.Gravity','TeleportService',
                   'AssemblyLinearVelocity','OnServerEvent','TouchEnded','Touched:Connect','PlayerAdded:Connect'):
  require(forbidden not in world and forbidden not in director,"forbidden authority "+forbidden)
 for name in ('WF-13','WF-14','WF-15','3秒理解','Counterplay','Counterplay'.lower(),'反撃','対抗策'):
  if name.lower()=='counterplay':continue
  require(name in cards,"field design missing "+name)
 for text in ('S2+','NOT','未統合','安全','卵','無料'):
  require(text in cards,"honest design scope "+text)
 role=project["tree"]["ServerScriptService"]["G7_Fantasy_Realms"]
 require(role["RiftDirector"]["$path"]=="src/RiftDirector.luau","director Rojo wire")
 require(role["FieldShowcase"]["$path"]=="src/FieldShowcase.server.luau","showcase Rojo wire")
 require("ReplicatedStorage" not in project["tree"] and "StarterPlayer" not in project["tree"],"not a hidden S1 game")
 return True
if __name__=="__main__":
 check_source();check_contract()
 print("G7_STUDIO_ONLY_3_ORIGINAL_REALM_DESIGN_AND_COSMETIC_SOURCE_LOCK_PASS")

