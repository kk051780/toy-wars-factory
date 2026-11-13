// EGG RAID RUMBLE independent V4 vs old earned-power source QA.
// Static canonical source invariants only; cannot establish Roblox engine behavior.
import {readFileSync} from "node:fs";
import {pathToFileURL} from "node:url";
import {analyze,gitBlobSha} from "./audit_horde_respawn.mjs";

export const pins = Object.freeze({
  v2Full:"55ad13b45907a5a3e9deae7196a7c202a0672c0c",
  v4Full:"376e943673dc089a5381e0d46570b92185a5d32a",
  oldPowerFull:"cb2540dc4a3e5b819c0e3598d4af5e2b6dca76d3",
  v2HordeBlob:"c1ef565f4e8b11a6e8ff7eac5ed55c8f268a4553",
  v4HordeBlob:"7edfda9e5a1d4ac8ae47d66ea7cf908eb8e4af6e",
  v2GameBlob:"f8c45bcf109dc3229c0459e4fb9fa224ab6c38a4",
  v4GameBlob:"fba78a510ba7f9044cd7ce7a6d40b69ee59c1a03",
  powerGameBlob:"ac995ea5e960942a557ee0a2a4116bff8ceadfe8",
  powerAssemblerBlob:"04f89fa61f773ecd3342c969a9e354ed6703170e"
});

export function inspectHorde(source) {
  const old=analyze(source);
  const c=source.replace(/--[^\n]*/g,"");
  const groundNames=c.includes('world:FindFirstChild("GrassArena")')
    && c.includes('world:FindFirstChild("CenterRoad")');
  const dynamicGround=c.includes("local feetY=groundTop(self.world,x,z)")
    && c.includes("local base=Vector3.new(x,feetY+halfBody,z)");
  const footStable=groundNames && dynamicGround;
  const reentry=old.safe && c.includes("m.attackAt=now+1.5")
    && c.includes("m.flashUntil=0");
  return {gitBlob:gitBlobSha(source),groundNames,dynamicGround,footStable,
    eliteDeathAndRespawnSafe:old.safe, reentry, safe:footStable&&reentry};
}
export function inspectGame(source) {
  const c=source.replace(/--[^\n]*/g,"");
  const first=c.indexOf("local function applyAttack(");
  const next=first>=0?c.indexOf("\nlocal function ",first+20):-1;
  if(first<0||next<0)throw Error("GAME_ATTACK_ANCHORS_MISSING");
  const attack=c.slice(first,next);
  const mob=attack.indexOf("horde:hit(");
  const gate=attack.indexOf("if mobHits>0 then return end");
  const core=attack.indexOf("match.hp[enemy] =");
  const mb=attack.includes("local mobHits = 0")&&attack.includes("mobHits=touched");
  const singleAttackCastlePriority=mb&&mob>=0&&gate>mob&&core>gate;
  const pvePower=attack.includes('earnedDamageMultiplier(player,"MINION")');
  const pvpPower=attack.includes('earnedDamageMultiplier(player,"PLAYER")');
  return {gitBlob:gitBlobSha(source),singleAttackCastlePriority,
    pvePower,pvpPower,safe:singleAttackCastlePriority};
}
export function inspectPowerBuilder(source) {
  const c=source.replace(/#[^\n]*/g,"");
  const staleBase=c.includes(pins.v2Full)&&c.includes(pins.v2GameBlob);
  const fixedParent=c.includes(pins.v4Full)&&c.includes(pins.v4GameBlob);
  const copiesOld=c.includes("shutil.copytree(OLD,DIST)");
  return {gitBlob:gitBlobSha(source),staleBase,fixedParent,copiesOld,
    safe:fixedParent&&!staleBase};
}
export function audit(horde,game,builder=null) {
  const h=inspectHorde(horde),g=inspectGame(game);
  const b=builder===null?null:inspectPowerBuilder(builder);
  return {horde:h,game:g,builder:b,
    safe:h.safe&&g.safe&&(b===null||b.safe)};
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href){
  const files=process.argv.slice(2);
  if(files.length!==2&&files.length!==3)
    throw Error("USAGE: node audit_v4_inheritance.mjs <Horde.luau> <Game.server.luau> [power_assemble.py]");
  const [h,g,b]=files.map(p=>readFileSync(p,"utf8"));
  const result=audit(h,g,b===undefined?null:b);
  console.log(JSON.stringify(result,null,2));
  if(!result.safe) process.exitCode=1;
}
