#!/usr/bin/env node
// Read-only and offline. Both refs must be present in the checked-out Git clone.
import {execFileSync} from "node:child_process";
import {createHash} from "node:crypto";
const refs={"official":{"ref":"rc/p0d-s1-kids-rc01","game":"releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau","hud":"releases/P0D_S1_KIDS_RC01/src/client/HUD.client.luau","game_sha":"7c5229f600f17537bc1bbbb0b96b6a2435875374","hud_sha":"ee594fbc34e6bf938518fae32c0642c852f11f9e"},"candidate":{"ref":"a0331e2e452f4e8e6530d32562ba5ff657b011d9","game":"handoffs/P0D-EGG-RUMBLE-H1-REAL-PROGRESSION-20261113-01/inputs/Game.server.luau","hud":"handoffs/P0D-EGG-RUMBLE-H1-REAL-PROGRESSION-20261113-01/inputs/HUD.client.luau","game_sha":"28a51605efcee572029154f978761622959df587","hud_sha":"6ef75cc76002e14b00cfb984cc799098e5cd033a"}};
function check(s){
 const e=[];
 const must=(text,token,id)=>{if(!text.includes(token))e.push(id)};
 if(s.og.split("\n").length!==703||s.cg.split("\n").length!==1583)e.push("GAME_LINE_DRIFT");
 if(s.oh.split("\n").length!==195||s.ch.split("\n").length!==420)e.push("HUD_LINE_DRIFT");
 for(const [tag,code]of [["O",s.og],["C",s.cg]]){
  if((code.match(/remote\.OnServerEvent:Connect\(/g)||[]).length!==1)e.push(tag+"_REMOTE_COUNT");
  must(code,"TrapRules.shouldTrigger",tag+"_TRAP");
  must(code,"PLACE_TRAP",tag+"_TRAP_ACTION");
  must(code,"startCanonical",tag+"_CANONICAL");
  must(code,'remote.Name = "TrapRaidersS1Remote"',tag+"_REMOTE_NAME");
 }
 for(const [id,tok]of Object.entries({
  VOTE:"ModeVote.tally(modeVotes,Players:GetPlayers())",
  MODE_GATED:"EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE",
  XP:"Progression.recordEvent",
  HATCH_SAVE:"PersistentHatch.settleProgress",
  SCOUT:"spawnActualScout",
  DEV_DB:'GetDataStore("EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1")'
 }))must(s.cg,tok,id);
 must(s.ch,"progressLastAward","LEVEL_HUD");
 must(s.ch,"MODE_VOTE","VOTE_HUD");
 must(s.ch,"GuardianTrap","TRAP_HUD");
 return e;
}
const get=(ref,path)=>execFileSync("git",["show",ref+":"+path],{encoding:"utf8",maxBuffer:5000000});
const blob=src=>{const b=Buffer.from(src,"utf8");return createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex")};
const guarded=(ref,path,sha)=>{const data=get(ref,path);if(blob(data)!==sha)throw Error("BLOB_DRIFT:"+path);return data};
try{
 const p=refs;const source={
  og:guarded(p.official.ref,p.official.game,p.official.game_sha),
  oh:guarded(p.official.ref,p.official.hud,p.official.hud_sha),
  cg:guarded(p.candidate.ref,p.candidate.game,p.candidate.game_sha),
  ch:guarded(p.candidate.ref,p.candidate.hud,p.candidate.hud_sha)
 };
 const errors=check(source);
 console.log(JSON.stringify({source_gate:errors.length?"FAIL":"PASS",errors,studio_verified:false,official_rc_adopted:false,publish_ready:false},null,2));
 if(errors.length)process.exitCode=2;
}catch(e){console.error(String(e));process.exitCode=3}
