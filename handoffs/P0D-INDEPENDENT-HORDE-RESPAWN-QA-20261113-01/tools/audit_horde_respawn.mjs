// Independent static source QA against exact original #288 Horde source.
// A source-code invariant detector: NEVER claim Roblox Studio runtime coverage.
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {pathToFileURL} from "node:url";

export const pinnedInput = {
  commit: "55ad13b45907a5a3e9deae7196a7c202a0672c0c",
  path: "handoffs/P0D-MUSOU-CHAOS-H1-20261113-01/inputs/MusouHorde.luau",
  gitBlob: "c1ef565f4e8b11a6e8ff7eac5ed55c8f268a4553"
};
function segment(s, from, to, name) {
  const a=s.indexOf(from);
  const b=a>=0?s.indexOf(to,a+from.length):-1;
  if(a<0 || b<0 || b<=a) throw new Error("SOURCE_ANCHOR_NOT_FOUND_"+name);
  return s.slice(a,b);
}
export function analyze(source) {
  if(typeof source!=="string") throw new Error("SOURCE_NOT_TEXT");
  const c=source.replace(/--[^\n]*/g,"");
  const hit=c.slice(c.indexOf("function Horde:hit("));
  const tick=c.slice(c.indexOf("function Horde:tick("));
  if(!hit.startsWith("function Horde:hit(")||!tick.startsWith("function Horde:tick(")) throw new Error("SCOPE_MISSING");
  const death=segment(hit,"if m.hp<=0 then","\n                    else","DEATH");
  const respawn=segment(tick,"if now>=m.deadUntil then","\n            end\n        else","RESPAWN");
  const has=(s,field,value)=>new RegExp("m\\."+field+"\\s*=\\s*"+value+"\\b").test(s);
  const deathTell=has(death,"tellUntil","0"), deathTarget=has(death,"target","nil");
  const respawnTell=has(respawn,"tellUntil","0"), respawnTarget=has(respawn,"target","nil");
  const eliteArmed=tick.includes("if m.elite and m.tellUntil>0 and now>=m.tellUntil");
  const blocked = !deathTell || !deathTarget || !respawnTell || !respawnTarget;
  return {
    safe:!blocked && eliteArmed,
    deathTell,deathTarget,respawnTell,respawnTarget,eliteArmed,
    requiresFix:blocked && eliteArmed
  };
}
export function gitBlobSha(source) {
  const content=Buffer.from(source,"utf8");
  const header=Buffer.from("blob "+content.length+"\0","utf8");
  return createHash("sha1").update(Buffer.concat([header,content])).digest("hex");
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href){
  const input=process.argv[2];
  const mode=process.argv[3]||"audit";
  if(!input) throw new Error("USAGE: node audit_horde_respawn.mjs <original-source-path> [expect-unsafe|expect-fixed]");
  const content=readFileSync(input,"utf8");
  const hash=gitBlobSha(content);
  if(hash!==pinnedInput.gitBlob && mode==="expect-unsafe") throw new Error("ORIGINAL_BLOB_DRIFT");
  const a=analyze(content);
  console.log(JSON.stringify({mode,sha:hash,...a}));
  if(mode==="expect-unsafe" && !a.requiresFix) throw new Error("ORIGINAL_UNSAFE_REGRESSION_NOT_REPRODUCED");
  else if(mode==="expect-fixed" && !a.safe) throw new Error("RESPAWN_TELEGRAPH_STILL_UNSAFE");
  else if(!["expect-unsafe","expect-fixed"].includes(mode) && !a.safe) process.exitCode=1;
}
