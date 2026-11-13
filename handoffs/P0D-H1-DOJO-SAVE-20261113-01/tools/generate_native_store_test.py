#!/usr/bin/env python3
"""Execute the ACTUAL assembled original Store+Dojo Luau under native CLI using mocked DataStore.
Only replace Roblox dependency imports with inert fixed test stubs. No copy/reimplementation
of the Store's actual save/validate/transition/update logic.
"""
from __future__ import annotations
import argparse
from pathlib import Path
HERE=Path(__file__).resolve()
REPO=HERE.parents[3];ROOT=HERE.parents[1]
DIST=ROOT/"dist/EGG_RAID_RUMBLE_H1_DOJO_DURABLE_DEV_PRIVATE"
store=(DIST/"src/server/PersistentHatchStore.luau").read_text("utf8")
dojo=(DIST/"src/server/DojoRules.luau").read_text("utf8")
assert store.rstrip().endswith("return Store")
assert dojo.rstrip().endswith("return Dojo")
store_imports={
'local Progression=require(script.Parent:WaitForChild("ProgressionRules"))':
'''local Progression={MAX_RECORDED_ROUNDS=2048,PLAYER_MAX_LEVEL=30,
    MASTERY_MAX_LEVEL=10,xpToNext=function(_lv) return 200 end,
    masteryToNext=function(_lv) return 100 end}''',
'local Evolution=require(script.Parent:WaitForChild("EvolutionRules"))':
'''local Evolution={MAX_FRAGMENTS=9999,MAX_ROUND_RECEIPTS=2048,
    MAX_EVOLUTION_RECEIPTS=2048}''',
'local Dojo=require(script.Parent:WaitForChild("DojoRules"))':
'''local Dojo=(function()
DOJO_RULES_PLACEHOLDER
end)()''',
}
for find,replace in store_imports.items():
 assert store.count(find)==1,(find,store.count(find))
 if "DOJO_RULES_PLACEHOLDER" in replace:
  replace=replace.replace("DOJO_RULES_PLACEHOLDER",dojo)
 store=store.replace(find,replace)
tests=r'''
local n=0
local function eq(name,got,want)
    n+=1
    if got~=want then
        error("DOJO_DURABLE_NATIVE_FAIL:"..name.." got="..tostring(got).." want="..tostring(want))
    end
end
local function truth(name,got) eq(name,got,true) end
local function missing(name,got) eq(name,got,nil) end
local uid=18945132
local original=Store.blank()
truth("legacy schema1 accepts no dojo",Store.validate(original))
missing("legacy optional dojo absent",original.dojo)
local old=Store.toDojoState(original)
truth("legacy becomes harmless runtime",old~=nil)
eq("old beast level1",old.level.BEAST,1)
eq("old weapon level1",old.level.WEAPON,1)
local s=Dojo.new()
for i=1,20 do truth("server training tick",Dojo.tick(s,"BEAST",1, i<5, true)) end
truth("beast leveled",s.level.BEAST>=2)
local snapshot=Store.dojoSnapshot(s)
truth("actual authorized snapshot",snapshot~=nil)
eq("snapshot excludes session current",snapshot.current,nil)
eq("snapshot excludes friend flag",snapshot.friendBonus,nil)
local Fake={value=nil,calls=0,callbackCalls=0}
function Fake:GetAsync(_key)
    return self.value
end
function Fake:UpdateAsync(key,cb)
    self.calls+=1
    eq("same original user key",key,"U_"..tostring(uid))
    local proposal=cb(self.value)
    self.callbackCalls+=1
    if proposal==nil then return nil end
    -- Roblox may invoke UpdateAsync callback multiple times; result must stay deterministic.
    local again=cb(self.value)
    self.callbackCalls+=1
    truth("callbacks yield same record",Store.validate(again))
    eq("same dojo revision on replay",again.dojo.revision,proposal.dojo.revision)
    self.value=proposal
    return proposal
end
local token="Dmy-test-session-id-20261113:1"
local ok,record,status=Store.persistDojo(Fake,uid,0,token,snapshot)
truth("real first atomic write",ok)
eq("real write receipt",record.dojo.lastToken,token)
eq("real dojo record revision",record.dojo.revision,1)
eq("profile overall revised",record.revision,1)
eq("first write state",status,"DOJO_PERSISTED_OR_ALREADY")
truth("record validates under legacy schema1",Store.validate(record))
local fresh=Store.toDojoState(record)
eq("beast level survives reload",fresh.level.BEAST,s.level.BEAST)
eq("weapon level unchanged",fresh.level.WEAPON,1)
eq("server friend bonus not saved",fresh.friendBonus,false)
local okReplay,same=Store.persistDojo(Fake,uid,0,token,snapshot)
truth("same token retry acknowledged",okReplay)
eq("same revision never double counted",same.dojo.revision,1)
eq("same profile revision never counted twice",same.revision,1)
local stale=Store.persistDojo(Fake,uid,0,"Dmy-test-session-id-20261113:2",snapshot)
eq("same session old revision rejected",stale,false)
local older=Dojo.new()
local rolled=Store.persistDojo(Fake,uid,1,"Dmy-test-session-id-20261113:3",Store.dojoSnapshot(older))
eq("rollback forbidden",rolled,false)
for i=1,24 do Dojo.tick(fresh,"WEAPON",1,false,true) end
local updatedSnapshot=Store.dojoSnapshot(fresh)
local ok2,saved2=Store.persistDojo(Fake,uid,1,"Dmy-test-session-id-20261113:4",updatedSnapshot)
truth("second skill saved atomically",ok2)
eq("second revision",saved2.dojo.revision,2)
truth("weapon leveled",saved2.dojo.level.WEAPON>=2)
eq("beast progress retained",saved2.dojo.level.BEAST,s.level.BEAST)
local grant,why=Store.grantTransition(saved2,"Smytestsession:1","forest_scout")
truth("existing hatch transition succeeds",grant~=nil)
eq("hatch receipt reason",why,"GRANTED")
eq("grant retains dojo revision",grant.dojo.revision,2)
eq("grant retains beast trained seconds",grant.dojo.trainedSeconds.BEAST,s.trainedSeconds.BEAST)
local equipped,how=Store.equipTransition(grant,"forest_scout")
truth("existing equip transition",equipped~=nil)
eq("equip keeps dojo",equipped.dojo.revision,2)
eq("equipped item changed",equipped.equipped,"forest_scout")
local corrupt=Store.blank()
corrupt.dojo={version=1,revision=-1,lastToken="",level={},xp={},trainedSeconds={}}
eq("invalid dojo never accepted",Store.validate(corrupt),false)
local badSnap=Store.dojoSnapshot({level={BEAST=50,WEAPON=1},
    xp={BEAST=0,WEAPON=0},trainedSeconds={BEAST=0,WEAPON=0}})
missing("level>5 rejected",badSnap)
missing("nan rejected",Store.dojoSnapshot({level={BEAST=1,WEAPON=1},
    xp={BEAST=0/0,WEAPON=0},trainedSeconds={BEAST=0,WEAPON=0}}))
eq("public/client fake userid rejected",Store.persistDojoTransition(saved2,-1,2,
    "Dmy-test-session-id-20261113:5",updatedSnapshot),nil)
local readOK,readRecord=Store.load(Fake,uid,nil)
truth("read persisted same key",readOK)
eq("reloaded combined same profile",readRecord.dojo.level.WEAPON,saved2.dojo.level.WEAPON)
-- Other auth transitions normalize the whole record and cannot silently wipe Dojo.
local normalized=Store.equipTransition(readRecord,"starter_scout")
eq("item changes never delete dojo",normalized.dojo.level.BEAST,s.level.BEAST)
assert(n>=67,n)
print("P0D_H1_DOJO_DURABLE_NATIVE_"..tostring(n).."_ASSERTIONS_PASS")
'''
assembled="local Store=(function()\n"+store+"\nend)()\n"+tests
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--write",required=True,type=Path)
 opts=p.parse_args()
 opts.write.parent.mkdir(parents=True,exist_ok=True)
 opts.write.write_text(assembled,encoding="utf8")
 print("DOJO_DURABLE_ORIGINAL_STORE_NATIVE_TEST_GENERATED",opts.write)
