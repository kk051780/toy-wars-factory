// P0D independent exact-scope source QA of #40 earned-evolution Game.
// Emits factual source-bound timings. Does NOT emulate Roblox Studio.
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
export const PIN={
  fullCommit:"1b21bf8e5fc6afa5c74813d7f1037f877e1273ed",
  gameGitBlob:"8b5fdf62f764ab6c963758d699cdfc681ed2ef96",
  hordeV4GitBlob:"7edfda9e5a1d4ac8ae47d66ea7cf908eb8e4af6e",
  v5HordeGitBlob:"8c147c801e7fa1ff362922d66c9a6fd432fc8b6e"
};
export function blob(source){
  const b=Buffer.from(source,"utf8");
  return createHash("sha1").update(Buffer.from("blob "+b.length+"\0")).update(b).digest("hex");
}
export function inspect(gameSource, hordeSource){
  if(typeof gameSource!=="string" || typeof hordeSource!=="string")throw Error("SOURCE_TEXT_REQUIRED");
  const scout=gameSource.match(/local\s+SCOUT_DURATION\s*=\s*(\d+)/);
  const guard=gameSource.match(/evolutionGuards\[player\]\s*=\s*\{untilAt=serverNow\(\)\+(\d+)/);
  const assault=gameSource.match(/nextEvolvedStrike=serverNow\(\)\+(\d+)/);
  if(!scout||!guard||!assault)throw Error("DURATION_SOURCE_ANCHORS_MISSING");
  const scoutSeconds=Number(scout[1]),guardSeconds=Number(guard[1]),assaultCooldownSeconds=Number(assault[1]);
  const clearsOnDespawn=gameSource.includes("evolutionGuards[player]=nil") &&
    gameSource.includes("while t<SCOUT_DURATION") &&
    gameSource.includes("cleanupScout(player)"); 
  const maxGuardSeconds=clearsOnDespawn?Math.min(scoutSeconds,guardSeconds):null;
  const guardMisstated=clearsOnDespawn&&guardSeconds>scoutSeconds;
  const v5WarningSnapshot=gameSource.includes("musouEliteWarningSeconds");
  const originalGame=blob(gameSource), actualHorde=blob(hordeSource);
  return {
    originalGameBlob:originalGame,actualHordeBlob:actualHorde,
    expectedGame:originalGame===PIN.gameGitBlob,
    expectedV4Horde:actualHorde===PIN.hordeV4GitBlob,
    containsV5Horde:actualHorde===PIN.v5HordeGitBlob,
    scoutSeconds,guardSeconds,assaultCooldownSeconds,clearsOnDespawn,
    maxGuardSeconds,guardMisstated,
    assaultAtMostOneAttemptPerSummon:assaultCooldownSeconds>scoutSeconds,
    v5WarningSnapshot
  };
}
if(process.argv[1]&&process.argv[1].endsWith("audit_40_scout_lifetime.mjs")){
  const [g,h]=process.argv.slice(2);
  if(!g||!h)throw Error("USAGE: node audit_40_scout_lifetime.mjs <Game.server.luau> <MusouHorde.luau>");
  const r=inspect(readFileSync(g,"utf8"),readFileSync(h,"utf8"));
  console.log(JSON.stringify(r,null,2));
  if(!r.expectedGame||!r.expectedV4Horde)throw Error("PINNED_SOURCE_MISMATCH");
  if(!r.guardMisstated)throw Error("EXPECTED_SOURCE_DEFECT_NOT_REPRODUCED");
}
