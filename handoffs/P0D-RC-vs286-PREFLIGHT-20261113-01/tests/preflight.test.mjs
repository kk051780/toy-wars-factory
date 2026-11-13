// Offline, source-backed mutation tests. Requires both git refs in local clone.
import assert from "node:assert/strict";
import {execFileSync} from "node:child_process";
const p={"official":{"ref":"rc/p0d-s1-kids-rc01","game":"releases/P0D_S1_KIDS_RC01/src/server/Game.server.luau","hud":"releases/P0D_S1_KIDS_RC01/src/client/HUD.client.luau","game_sha":"7c5229f600f17537bc1bbbb0b96b6a2435875374","hud_sha":"ee594fbc34e6bf938518fae32c0642c852f11f9e"},"candidate":{"ref":"a0331e2e452f4e8e6530d32562ba5ff657b011d9","game":"handoffs/P0D-EGG-RUMBLE-H1-REAL-PROGRESSION-20261113-01/inputs/Game.server.luau","hud":"handoffs/P0D-EGG-RUMBLE-H1-REAL-PROGRESSION-20261113-01/inputs/HUD.client.luau","game_sha":"28a51605efcee572029154f978761622959df587","hud_sha":"6ef75cc76002e14b00cfb984cc799098e5cd033a"}};
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
const src={og:get(p.official.ref,p.official.game),oh:get(p.official.ref,p.official.hud),cg:get(p.candidate.ref,p.candidate.game),ch:get(p.candidate.ref,p.candidate.hud)};
assert.deepEqual(check(src),[]);
const mutants=[
[x=>x.cg+="\nremote.OnServerEvent:Connect(function()end)","C_REMOTE_COUNT"],
[x=>x.cg=x.cg.replaceAll("TrapRules.shouldTrigger","MissingRule"),"C_TRAP"],
[x=>x.cg=x.cg.replaceAll("ModeVote.tally(modeVotes,Players:GetPlayers())","None"),"VOTE"],
[x=>x.cg=x.cg.replaceAll("EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE","EXPERIMENTAL_FIVE_EGG_MODE=chosenMode==ModeVote.SCORE"),"MODE_GATED"],
[x=>x.cg=x.cg.replaceAll("Progression.recordEvent","NoXP"),"XP"],
[x=>x.cg=x.cg.replaceAll("spawnActualScout","NoScout"),"SCOUT"],
[x=>x.ch=x.ch.replaceAll("progressLastAward","MissingLevel"),"LEVEL_HUD"],
[x=>x.og=x.og.replaceAll("PLACE_TRAP","OLD_ACTION"),"O_TRAP_ACTION"]
];
for(const [mutate,expected]of mutants){const s={...src};mutate(s);assert.ok(check(s).includes(expected),expected)}
console.log("P0D_STATIC_SOURCE_PREFLIGHT_9_OF_9_PASS");
