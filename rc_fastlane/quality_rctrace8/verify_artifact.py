#!/usr/bin/env python3
"""P0D GQ8 — independent ACTUAL official RC .rbxlx artifact-to-feature proof.

Read-only. No duplicate author/game implementation. This checks what was built
rather than just the selector's claim. Source/identity gate, NOT Studio gameplay,
Android, ART acceptance or FUN. Fail closed for RC-HEAD drift and false feature
flags. Works on a downloaded official Actions artifact, not a local preview.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

PLACE = "EGGRUMBLE_V3_RC31_CANONICAL_STUDIO.rbxlx"
RECEIPT = "EGGRUMBLE_V3_OFFICIAL_RC31_RECEIPT.json"
N = 31

# A selected original source may own several features. This is a literal
# source-to-artifact contract, NOT a test of engine movement/visual quality.
RULES = {
 "characters": {
  "EGGRUMBLE_SevenRoleCombat": (
    'local ORDER={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}',
    "local function execute(",
  )},
 "field": {
  "EGGRUMBLE_BotPathRouter": (
    "local ray=workspace:Raycast(at,diff.Unit*diff.Magnitude,p)",
  ),
  "EGGRUMBLE_LobbyCastleModesPreview": (
    "CastleAccessRamp",
    'local rowZ=if mode=="TEAM" then {338,506,610} else {338,448,676}',
    "local rareFieldEgg=i==4 or i==5",
  ),
 },
 "battle": {
  "EGGRUMBLE_SevenRoleCombat": (
    "GQ_DEAD_CASTER_FENCE:", "currentHumanMember(session,",
  )},
 "castle": {
  "EGGRUMBLE_LobbyCastleModesPreview": (
    "Rules.depositEggs(", "joined[actor.UserId]==mode", "coreBoard.MaxDistance=65",
    "vaultBoard.MaxDistance=40",
  )},
 "neutral": {
  "EGGRUMBLE_NeutralStoneGiant": ("hpGui.MaxDistance=55", "hpGui.AlwaysOnTop=false"),
  "EGGRUMBLE_SwarmCombat": (
    "candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)",
    "session.neutralBudget:acquire(",
  )},
 "items": {
  "EGGRUMBLE_FieldItemPickups": (
    'interactionGuard.allow(player,part,"拾う",part.Name)',
    "local function restoreSpeed()",
    "if not healUseful(kind,hum.Health,hum.MaxHealth) then return end",
  )},
 "lobby": {
  "EGGRUMBLE_LobbyCastleModesPreview": (
    'joinQueue("TEAM",p)', 'joinQueue("BATTLE_ROYALE",p)',
    "local function nearbyBoard(", "session.isCurrentHuman=function",
  )},
 "balance": {
  "EGGRUMBLE_CastleMatchRules": ("M.MAX_HERO_SLOTS=16",
   "limit>=2 and limit<=M.MAX_HERO_SLOTS",
   "#roster>=2 and #roster<=M.MAX_HERO_SLOTS"),
 "EGGRUMBLE_CombatBalance": ("return Balance",),
  "EGGRUMBLE_MatchResultService": ("function ResultRetry.deliver(",
   'local status=if session.rules.winner=="DRAW" then "引き分け"',),
  "EGGRUMBLE_ScoreBalance": ("local claimedRareFieldEggs={}",),
 },
}
ROLE_CLASSES = {
 "EGGRUMBLE_LobbyCastleModesPreview": "Script",
 "EGGRUMBLE_SevenRoleCombat": "ModuleScript",
 "EGGRUMBLE_SwarmCombat": "ModuleScript",
 "EGGRUMBLE_BotActors": "ModuleScript",
 "EGGRUMBLE_BotPathRouter": "ModuleScript",
 "EGGRUMBLE_FieldItemPickups": "ModuleScript",
 "EGGRUMBLE_CastleMatchRules": "ModuleScript",
 "EGGRUMBLE_MatchResultService": "ModuleScript",
 "EGGRUMBLE_CombatFeel": "LocalScript",
 "EGGRUMBLE_NeutralStoneGiant": "ModuleScript",
}
# These 61 enabled RC31 flags are mapped to source evidence (not Studio gameplay proof).
# A future new flag is not silently certified; report it as unassessed.
FEATURE_EVIDENCE = {
 "GQ8_ITEM_CARGO_SLOW_RECHECK_20261118": ("EGGRUMBLE_FieldItemPickups", ("GQ8_ITEM_CARGO_SLOW_RECHECK_20261118", "if carryingEnemyEggs(player,session) then", "cancelBuffIfCarrier(player,5,restoreSpeed)")),
 "GQ8_REPLAY_RESET_RETRY_SESSION_FENCE_20261118": ("EGGRUMBLE_RoundReplay","-- GQ8_REPLAY_RESET_RETRY_SESSION_FENCE_20261118"),
 "GQ8_STONE_GIANT_NEARBY_TRUE_HP_20261118": ("EGGRUMBLE_NeutralStoneGiant", ("-- GQ8_STONE_GIANT_TRUE_HP_LABEL_20261118", "hpGui.MaxDistance=55", 'model:SetAttribute("EGGRUMBLE_BossHealth",health)', 'hpText.Text="石巨人 "..tostring(math.floor(health)).." / 900"')),
 "GQ8_BOSS_RESULT_TRUE_CREDIT_20261118": ("EGGRUMBLE_MatchResultService","-- GQ8_BOSS_RESULT_TRUE_CREDIT_20261118"),
 "GQ8_RESULT_MOBILE_READABILITY_20261118": ("EGGRUMBLE_MatchResultService", (
   "-- GQ8_RESULT_MOBILE_READABILITY_20261118",
   "statsLabel.TextScaled=false",
   "statsLabel.TextSize=15",
   "statsLabel.TextWrapped=true",
   'statsLabel.Text=stats:gsub(" 納","\\n納",1)',
 )),
 "DEAD_CASTER_FENCE_530": ("EGGRUMBLE_SevenRoleCombat","GQ_DEAD_CASTER_FENCE:"),
 "HUMAN_MATCH_MEMBERSHIP_535": ("EGGRUMBLE_SevenRoleCombat","currentHumanMember(session,"),
 "HUMAN_BOT_MATCH_MEMBERSHIP_531": ("EGGRUMBLE_LobbyCastleModesPreview","session.isCurrentHuman=function"),
 "NEUTRAL_MELEE_533": ("EGGRUMBLE_SwarmCombat","candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"),
 "SHARED_NEUTRAL_BUDGET_528": ("EGGRUMBLE_SwarmCombat","session.neutralBudget:acquire("),
 "NEUTRAL_NEAREST_ELIGIBLE_FALLBACK_541": ("EGGRUMBLE_SwarmCombat","candidate.victim.humanoid:TakeDamage(Melee.DAMAGE)"),
 "CASTLE_EGG_DEPOSIT_REFRESH_537": ("EGGRUMBLE_LobbyCastleModesPreview","session.refresh()"),
 "ASSASSIN_RESPAWN_STEALTH_FENCE_540": ("EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_StealthUntil"),
 "LOBBY_NEARBY_BOARDS_539": ("EGGRUMBLE_LobbyCastleModesPreview","gui.MaxDistance=math.clamp(maxDistance,16,52)"),
 "ORIGINAL_ITEM_AUTHOR_489": ("EGGRUMBLE_FieldItemPickups",'interactionGuard.allow(player,part,"拾う",part.Name)'),
 "BOT_NEAREST_CURRENT_HUMAN_555": ("EGGRUMBLE_BotActors","nearestHumanoid:TakeDamage(BOT_HERO_DAMAGE)"),
 "BOT_ROUTE_FULLSTEP_536": ("EGGRUMBLE_BotPathRouter","local ray=workspace:Raycast(at,diff.Unit*diff.Magnitude,p)"),
 "CASTLE_EGG_BOARD_DISTANCE_547": ("EGGRUMBLE_LobbyCastleModesPreview","coreBoard.MaxDistance=65"),
 "CARRIER_STALE_AVATAR_DIED_FENCE_551": ("EGGRUMBLE_LobbyCastleModesPreview","player.Character~=character"),
 "RESULT_GUI_BOUNDED_RETRY_538": ("EGGRUMBLE_MatchResultService","function ResultRetry.deliver("),
 "FIELD_EGGS_CASTLE_FOUNDATION_CLEARANCE_523": (
   "EGGRUMBLE_LobbyCastleModesPreview",
   'local rowZ=if mode=="TEAM" then {338,506,610} else {338,448,676}'),
 "ROSTER16_HARDCAP_583": ("EGGRUMBLE_CastleMatchRules","#roster>=2 and #roster<=M.MAX_HERO_SLOTS"),
 "HEAL_NO_WASTE_517": ("EGGRUMBLE_FieldItemPickups",
  "if not healUseful(kind,hum.Health,hum.MaxHealth) then return end"),
 "VERTICAL_HIT_FAIRNESS_595": ("EGGRUMBLE_AttackGeometry",
  "if dy~=dy or math.abs(dy)>math.min(radius,14) then return false end"),
 "NEUTRAL_DEATH_KO_CURRENT_OWNER_508": ("EGGRUMBLE_SwarmCombat",
  "and KoFence.mayCredit(session,id,m,all) then"),
 "AI_TAKEOVER_TERMINAL_FENCE_580": ("EGGRUMBLE_BotActors",
  'if session.rules.phase~="ACTIVE" or not folder.Parent then return false end'),
 "TEAM_FIELD_ITEM_RIDGE_FOREST_CLEARANCE_520": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "CentralRidgeRight",
  "local z=470+math.floor(n/4)*110+(if n==1 then 18 else 0)")),
 "FIELD_CARRIER_OFFARENA_DROP_515": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "function Drop.recover(",
  "DropBounds.recover(mode,root.X,root.Z,at.X,at.Z,")),
 "ZOMBIE_COMMAND_SQUAD_582": ("EGGRUMBLE_SevenRoleCombat", (
  "local ZombieCommander=",
  "ZombieCommander.begin(p,")),
 "DEPOSIT_CURRENT_SESSION_586": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "GQ_DEPOSIT_CURRENT_MATCH_586",
  "joined[p.UserId]~=session.mode",
  "sessions[session.mode]~=session")),
 "ZOMBIE_NEUTRAL_STABLE_ID_V3": ("EGGRUMBLE_SevenRoleCombat", (
  'local neutralIds=setmetatable({}, {__mode="k"})',
  "local function neutralTargetId(enemy:Model):string",
  'id=neutralTargetId(enemy),kind="NEUTRAL"')),
 "SERVER_PROMPT_CONFIG_REACH_611": ("EGGRUMBLE_InteractionGuard", (
  "local reach=configuredReach(part,verb)",
  "if selected then return nil end",
  "reach+EXCESS_RADIUS")),
 "BEAST_REAL_ESCORT_618": ("EGGRUMBLE_SevenRoleCombat", (
  "function BeastEscort.begin(session:any, player:Player",
  "if BeastEscort.begin(session,p,char,root,h,owner,function(",
  "hum:MoveTo(targetRoot.Position)",
  "neutralAndBotHit(session,p,petRoot,pet,at,3.5,6,def.color,spec.shape)")),

 "ZOMBIE_GUARD_CASTLE_LEASH_582": ("EGGRUMBLE_SevenRoleCombat", (
  "local GUARD_LEASH = 12",
  "distance(unit, guardAnchor) > GUARD_LEASH",
  "distance(candidate, guardAnchor) <= GUARD_LEASH")),
 "LOBBY_QUEUE_ETA_615": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "local queueStartedAt:{[string]:number}={}",
  "local function refreshQueueBoard(mode:string)",
  "label.Text=prefix..",
  "refreshQueueBoard(previous)",
  "if #queues[mode]==0 then queueStartedAt[mode]=nil end")),
 "BOSS_SHOCKWAVE_WALL_OCCLUSION_518": ("EGGRUMBLE_NeutralStoneGiant", (
   "local function shockwaveClear(character:Model?,root:BasePart):boolean",
   "params.RespectCanCollide=true",
   "and shockwaveClear(c,root) then")),
 "BUILDER_WALL_SERVER_TOOL_522": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "-- GQ522_ORIGINAL_BUILDER_WALL_ONLY_INLINE_RC31",
  "BuilderConstruction.equip(session,p,true,false)",
  "BuilderConstruction.clear(session)",
  "Policy.LIFETIME=9",
  "Policy.MAX_PER_HERO=2",
  "Policy.MAX_PER_SESSION=12",
  "tool.Activated:Connect(function()")),
 "GQ8_ROLE_SELECTION_ACK_20261117": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "-- GQ8_ROLE_SELECTION_ACK_BEGIN",
  'if chosenRole[p.UserId]==nil then',
  'p:SetAttribute("EGGRUMBLE_RoleSelectionRequired",true)',
  'p:SetAttribute("EGGRUMBLE_RoleSelectionRequired",nil)',
  "職業選択後｜チーム戦（再操作で解除）",
  "職業選択後｜BR戦（再操作で解除）")),
 "GQ646_LOBBY_SAFE_SPAWN_20261117": ("EGGRUMBLE_LobbyCastleModesPreview", (
   "-- GQ646_LOBBY_SAFE_SPAWN_BEGIN",
   "lobbyGround.CanCollide=true",
   "lobbySpawn.Neutral=true",
   "if mode and sessions[mode] then return end")),
 "RARE_FIELD_EGG_SCORE_20261117": ("EGGRUMBLE_ScoreBalance", (
   "RARE_FIELD_EGG_CAP=2, RARE_FIELD_EGG_RATE=60",
   "local claimedRareFieldEggs={}",
   'id=="FIELD_4" or id=="FIELD_5"')),
 "MATCH_DEADLINE_DRAW_499": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "local deadlineLease=Deadline.new(os.clock(),deadlineId)",
  "Deadline.expire(session.rules,deadlineLease,os.clock(),deadlineId)",
  "session.refresh() -- existing result/round replay",
  'state.winner="DRAW"',
  'type="TIME_LIMIT_DRAW"')),


 "GQ514_BOSS_KO_ROUND_RESET_20261117": ("EGGRUMBLE_RoundReplay",
  'p:SetAttribute("EGGRUMBLE_BossDefeats",0)'),
 "GQ524_NINJA_TRAPPER_WARP_CLEARANCE_20261117": ("EGGRUMBLE_SevenRoleCombat", (
  "local function safeMove(session:any,char:Model,root:BasePart,amount:number):boolean",
  'session.world:FindFirstChild("TacticalBattlefield")',
  "for _,height in ipairs({-1.1,2,4.6}) do",
  "for _,side in ipairs({-1.3,0,1.3}) do",
  "if distance<3 then return false end",
  "workspace:GetPartBoundsInBox(",
  "Vector3.new(3.2,4.5,3.2)",
  "if part.CanCollide then return false end",
  "safeMove(session,char,root,25)",
  "safeMove(session,char,root,20)")),
 "GQ505_SERVER_MODE_FX_FAIR_INLINE31": ("EGGRUMBLE_SkillFX", (
  "local ModeFairQuota=(function()",
  "function Quota.new(totalCap:number,reserve:number)",
  "local fairQuota=ModeFairQuota.new(72,12)",
  "fairQuota:acquire(parent.Name)",
  "fairQuota:release(lease)",
  "fairQuota:canStart(parent.Name,MAX_NEW_PER_PULSE)",
  "self.usage[mode]-=1")),
 "GQ510_MAGE_TEAM_AI_WALL_LOS_20261117": ("EGGRUMBLE_SevenRoleCombat", (
  "local sourceCharacter=player.Character",
  "and (other==player or lineClear(root.Position+Vector3.new(0,1.5,0),",
  "botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)",
  'if session.mode=="TEAM" then')),
 "GQ506_RESPAWN_GRACE_SINGLE_HOST_20261117": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "GQ506_RESPAWN_GRACE_SINGLE_HOST_20261117",
  'local GRACE_SECONDS = 2.25',
  'local RESPAWN_TICKET_SECONDS = 12',
  'local MAX_HOME_DISTANCE = 85',
  'local function currentArena(player: Player, character: Model)',
  'local function originArena(player: Player, character: Model)',
  'if not ticket or os.clock() > ticket.expiresAt then return end',
  'currentArena(player, character) ~= ticket.arena',
  'if player:GetAttribute("EGGRUMBLE_QueuedMode") ~= ticket.mode then return end',
  'tickets[player] = nil',
  'humanoid.Died:Connect(function()',
  'Instance.new("ForceField")',
  'if instance:IsA("Tool") then revoke() end',
  'ProximityPromptService.PromptTriggered:Connect',
  'if state.shield.Parent then state.shield:Destroy() end',
  'task.delay(GRACE_SECONDS, revoke)')),
 "GQ504_ORIGINAL_CONFIRMED_HIT_AUDIO_INLINE_20261117": ("EGGRUMBLE_CombatFeel", (
  "GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117",
  'local GROUP="EGGRUMBLE_GQ_ConfirmedHitAudio"',
  "local MAX_VOICES=4",
  "local MAX_PER_WINDOW=6",
  "local MAX_VOLUME=.30",
  'local onHit=player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(confirmedHit)',
  'GetAttributeChangedSignal("EGGRUMBLE_SFXMuted")',
  'GetAttributeChangedSignal("EGGRUMBLE_Eliminated")',
  "local function confirmedHit()",
  "onCharacterRemoving=player.CharacterRemoving:Connect",
  "GQ504_CONFIRMED_HIT_AUDIO_INLINE_END_20261117")),
 "GQ8_CASTLE_DEFENSE_CURRENT_HUMAN_20261117": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "-- GQ8_CASTLE_DEFENSE_CURRENT_HUMAN_20261117",
  "session.isCurrentHuman(player)~=true then",
  "session.isCurrentHuman(closest.player)~=true) then return end")),
 "GQ8_V3_SERVER_ACCEPTED_CAST_CUE_20261117": ("EGGRUMBLE_CombatFeel", (
  "-- GQ8_V3_SERVER_ACCEPTED_CAST_CUE_20261117 BEGIN",
  'player:GetAttributeChangedSignal("EGGRUMBLE_SkillCastSignature")',
  "ServerAcceptedCastCue",
  "if not tones[role] then return end",
  "if not hum or hum.Health<=0 then return end",
  "CAST_CUE_MIN_GAP=.12",
  "-- GQ8_V3_SERVER_ACCEPTED_CAST_CUE_20261117 END")),
 "GQ8_FIELD_EGG_CREATION_LIMIT_20261118": ("EGGRUMBLE_CastleMatchRules", (
  "M.MAX_FIELD_EGGS=512",
  "and m.fieldEggs<=M.MAX_FIELD_EGGS",
  "invalid egg count")),
 "GQ732_CASTLE_DUPLICATE_DECOR_SLOT_20261117": ("EGGRUMBLE_CastleMatchRules", (
  "duplicate decoration in this plot",
  "existing.kind==piece.kind",
  "existing.x==piece.x",
  "existing.y==piece.y",
  "existing.z==piece.z")),
 "GQ500_ORIGINAL_LIVE_CASTLE_DEFENSE_INLINE_20261117": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "local CastleDefense=(function()",
  "Policy.TICK_SECONDS=0.35",
  "Policy.MAX_CASTLES=16",
  "Policy.canTarget(",
  "Policy.mayActivate(",
  "Policy.canAcquire(",
  "closest.hum:TakeDamage(Policy.CONFIG[kind].damage)",
  "session.castleDefenseStop=stop",
  "CastleDefense.start(session)")),
 "GQ496_OBJECTIVE_COMPASS_CURRENT31_20261117": ("EGGRUMBLE_CombatFeel", (
  "GQ496_OBJECTIVE_COMPASS_CURRENT31_20261117",
  'gui.Name="EGGRUMBLE_GQ_ObjectiveCompass"',
  'local function isEnemy(mode:string, own:Model, other:Model, arena:Instance):boolean',
  'if mode~="TEAM" then return false end',
  'if homeSelected then',
  'local function pickObjective(',
  'local function nearestActiveItem(',
  'EGGRUMBLE_FieldItems',
  'NEUTRAL_BOSS_STONE_GIANT',
  'return home,"自城へ帰還（手動）"',
  'UPDATE_SECONDS = 0.8',
  'INITIAL_SECONDS = 18',
  'marker.AlwaysOnTop=false',
  'RunService.Heartbeat:Connect(function(dt:number)')),
 "GQ503_SEVEN_ROLE_SECONDARY_FX_LOD_20261117": ("EGGRUMBLE_CombatFeel", (
  "GQ503_SEVEN_ROLE_SECONDARY_FX_LOD_20261117",
  "WarGod_FlyingSlash=true, Mage_CrystalStorm=true, Assassin_ShadowAfterimage=true",
  "local function fxShouldHide(kind:string,distance:number,touch:boolean",
  "if distance<=40 then return false end",
  "if fxElapsed<.22 then return end",
  "part.LocalTransparencyModifier=if hidden then 1 else record.original")),
 "GQ511_ORIGINAL_CARRIER_WORLD_TELL_INLINE_20261117": ("EGGRUMBLE_LobbyCastleModesPreview", (
  'local CarrierWorldTell=(function()',
  'Policy.MAX_WORLD_VIEW_DISTANCE = 70',
  'gui.AlwaysOnTop = false',
  'gui.MaxDistance = Policy.MAX_WORLD_VIEW_DISTANCE',
  'session.world:FindFirstChild("TacticalBattlefield")',
  'session.carrierWorldTellEnabled == false',
  'CarrierWorldTell.start(session)')),
 "GQ8_CASTLE_PROMPT_CURRENT_MATCH_20261117": ("EGGRUMBLE_LobbyCastleModesPreview", (
  "if joined[p.UserId]~=session.mode or sessions[session.mode]~=session",
  "if not session.rules or tostring(p.UserId)~=entry.id",
  "if not session.rules or joined[p.UserId]~=session.mode",
  "or sessions[session.mode]~=session or type(session.isCurrentHuman)",
  "or session.isCurrentHuman(p)~=true then return end")),
 "GQ512_ROUND_COMBO_REPLAY_RESET_20261117": ("EGGRUMBLE_RoundReplay", (
  'p:SetAttribute("EGGRUMBLE_Combo",0)',
  'p:SetAttribute("EGGRUMBLE_BestCombo",0)',
  'p:SetAttribute("EGGRUMBLE_NeutralKOs",0)')),
 "GQ81_CONFIRMED_HIT_042_V3_PORT_20261117": ("EGGRUMBLE_CombatFeel", (
  "hitToast.Name=\"ConfirmedHit042\"",
  "task.delay(.42,function()",
  "if thisPulse==pulse and hitToast.Parent then hitToast.Visible=false end",
  'player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")')),
 "POSTWIN_LATE_CARRIER_DEATH_FREEZE_509": ("EGGRUMBLE_CastleMatchRules",
  'if m.phase~="ACTIVE" or m.winner~=nil then return 0,{} end'),
 "BOT_SIEGE_TARGET_PACING_527": ("EGGRUMBLE_BotActors", (
  "Pace.MIN_SECONDS_PER_CASTLE = 7.0",
  "SiegePacing.allow(session,enemy.id,id,now)",
  "SiegePacing.cancelFailed(session,enemy.id,id,now)",
  "local SiegePacing=(function()")),

}

# This security contract spans existing authoritative Host and Item scripts.
# One-side-only marker is not enough to certify item session isolation.
CROSS_SCRIPT_FEATURE_EVIDENCE = {
 "ITEM_CURRENT_SESSION_525": {
  "EGGRUMBLE_LobbyCastleModesPreview": (
   "session.canCollectWorldItem=function(actor:Player):boolean",
   "sessions[mode]==session",
   "joined[actor.UserId]==mode"),
  "EGGRUMBLE_FieldItemPickups": (
   "local authorize=session.canCollectWorldItem",
   "pcall(authorize,player)",
   "if not ok or allowed~=true then return false end"),
 },
}

class RedGate(ValueError):
    pass

def require(condition:bool, reason:str):
    if not condition:
        raise RedGate("RED_GQ8_"+reason)

def source_scripts(place:bytes):
    root=ET.fromstring(place)
    found={}
    for node in root.iter("Item"):
        klass=node.attrib.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"):
            continue
        props=node.find("Properties")
        require(props is not None,"SCRIPT_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        content=props.findtext("ProtectedString[@name='Source']")
        if content is None:
            content=props.findtext("string[@name='Source']")
        require(bool(name) and content is not None,"SCRIPT_NAME_OR_SOURCE")
        require(name not in found,"DUPLICATE_SCRIPT_"+str(name))
        found[name]=(klass,content.replace("\r\n","\n"))
    require(len(found)==N,"SCRIPT_COUNT_31_"+str(len(found)))
    for name,klass in ROLE_CLASSES.items():
        require(name in found and found[name][0]==klass,"ROLE_CLASS_"+name)
    return found

def verify(place:bytes, receipt:dict, manifest:dict, active:dict, expected_head:str,
           allow_pr_premerge:bool=False):
    require(len(expected_head)==40 and all(c in "0123456789abcdef" for c in expected_head),
            "EXPECTED_COMMIT_SHA_INVALID")
    require(manifest["canonical_branch"]=="rc/p0d-s1-kids-rc01","CANONICAL_BRANCH")
    require(manifest["profile"]=="eggrumble_v3_31" and manifest["source_count"]==N,
            "ACTIVE_SOURCE_PROFILE_OR_COUNT")
    require(manifest["enabled"] is True,"V3_COMPANION_NOT_ENABLED")
    require(active["active_profile"]=="rich51","S1_LEGACY_CHANGED_WITHOUT_OWNER")
    require(active["source_profiles"]["eggrumble_v3_31"]["source_count"]==N,
            "S1_RC_PROFILE_NOT_REGISTERED")
    require(receipt.get("canonical_branch")=="rc/p0d-s1-kids-rc01",
            "ARTIFACT_NOT_CANONICAL")
    require(receipt.get("github_commit_sha")==expected_head,"ARTIFACT_STALE_WRONG_HEAD")
    official=receipt.get("official_rc_commit_verified") is True
    if not official:
        require(allow_pr_premerge and
                receipt.get("status")=="RC_PREMERGE_COMPANION_PROFILE_BUILD_PASS_NOT_STUDIO_PLAYTESTED",
                "NOT_OFFICIAL_PUSH")
    else:
        require(receipt.get("status")=="CANONICAL_RC_BRANCH_COMPANION_PROFILE_BUILD_PASS_NOT_STUDIO_PLAYTESTED",
                "OFFICIAL_PUSH_CLAIM_MISMATCH")
    require(receipt.get("release_profile")=="eggrumble_v3_31","ARTIFACT_NOT_V3")
    require(receipt.get("script_count")==N and receipt.get("script_source_and_class_exact")=="31/31",
            "ARTIFACT_SOURCE_RECEIPT_NOT_PASS")
    require(receipt.get("roblox_publish") is False,"UNAUTHORIZED_PUBLISH")
    require(receipt.get("s1_active_profile_unchanged") is True,"S1_MUTATION")
    require(receipt.get("source_author_heads")==manifest.get("source_heads"),
            "AUTHOR_SHA_MANIFEST_ARTIFACT_DRIFT")
    require(receipt.get("place_name")==PLACE,"ARTIFACT_PLACE_NAME")
    require(receipt.get("place_size_bytes")==len(place),"PLACE_BYTES_WRONG")
    placehash=hashlib.sha256(place).hexdigest()
    require(receipt.get("place_sha256")==placehash,"PLACE_SHA256_WRONG")
    scripts=source_scripts(place)
    by_domain={}
    for domain,targets in RULES.items():
        for name,needles in targets.items():
            require(name in scripts,"DOMAIN_"+domain+"_MISSING_"+name)
            for anchor in needles:
                require(anchor in scripts[name][1],"DOMAIN_"+domain+"_MISSING_"+name+"_"+anchor[:24])
        by_domain[domain]="SOURCE_ANCHOR_PRESENT_NOT_STUDIO_VERIFIED"
    flags=manifest.get("feature_flags",{})
    require(isinstance(flags,dict),"FEATURE_FLAGS_NOT_MAPPING")
    # A new enabled flag without explicit actual-Place source evidence is RED,
    # not a merely visible YELLOW field in an otherwise successful RC receipt.
    # A disabled unknown flag may remain as PREP without claiming its activation.
    for flag,state in flags.items():
        require(type(state) is bool,"FEATURE_FLAG_NOT_BOOLEAN_"+flag)
        if state:
            require(flag in FEATURE_EVIDENCE,"ENABLED_FLAG_WITHOUT_SOURCE_EVIDENCE_"+flag)
    for flag,(script,anchors) in FEATURE_EVIDENCE.items():
        require(flags.get(flag) is True,"FEATURE_FLAG_DISABLED_OR_UNKNOWN_"+flag)
        require(script in scripts,"FEATURE_SOURCE_MISSING_"+flag)
        required=(anchors,) if isinstance(anchors,str) else anchors
        require(bool(required),"FEATURE_SOURCE_EMPTY_"+flag)
        for anchor in required:
            require(anchor in scripts[script][1],"FEATURE_FALSE_ON_"+flag)
    for flag,owners in CROSS_SCRIPT_FEATURE_EVIDENCE.items():
        require(flags.get(flag) is True,"FEATURE_FLAG_DISABLED_OR_UNKNOWN_"+flag)
        for script,anchors in owners.items():
            require(script in scripts,"FEATURE_FALSE_ON_"+flag+"_"+script)
            for anchor in anchors:
                require(anchor in scripts[script][1],"FEATURE_FALSE_ON_"+flag+"_"+script)
    return {
        "result":("OFFICIAL_SOURCE_ARTIFACT_8_DOMAIN_GATE_PASS_NOT_GAMEPLAY_ACCEPTANCE"
                  if official else "PR_PREMERGE_SOURCE_ARTIFACT_GATE_PASS_NOT_OFFICIAL_RC"),
        "official_rc_push_verified":official,
        "official_rc_head":expected_head,"studio_place_bytes":len(place),
        "studio_place_sha256":placehash,"script_count":len(scripts),
        "domains":by_domain,
        "verified_flag_count":len(FEATURE_EVIDENCE)+len(CROSS_SCRIPT_FEATURE_EVIDENCE),
        "unassessed_new_flags":sorted(set(flags)-set(FEATURE_EVIDENCE)-set(CROSS_SCRIPT_FEATURE_EVIDENCE)),
        "legacy_s1_default":"rich51",
        "real_studio_2client":"NOT_TESTED",
        "android_15min":"NOT_TESTED","owner_fun":"NOT_TESTED",
        "roblox_published":False,
    }

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--artifact-dir",required=True,type=Path)
    cli.add_argument("--manifest",required=True,type=Path)
    cli.add_argument("--active",required=True,type=Path)
    cli.add_argument("--rc-head",required=True)
    cli.add_argument("--out",required=True,type=Path)
    cli.add_argument("--pr-premerge",action="store_true")
    a=cli.parse_args()
    data=a.artifact_dir.resolve(strict=True)
    place=(data/PLACE).read_bytes()
    receipt=json.loads((data/RECEIPT).read_text(encoding="utf-8"))
    manifest=json.loads(a.manifest.read_text(encoding="utf-8"))
    active=json.loads(a.active.read_text(encoding="utf-8"))
    result=verify(place,receipt,manifest,active,a.rc_head,allow_pr_premerge=a.pr_premerge)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                     encoding="utf-8")
    print(("GQ8_OFFICIAL_PLACE_8_DOMAINS_SOURCE_ANCHOR_AND_"
           +str(result["verified_flag_count"])+"_FEATURE_FLAGS_PASS")
          if result["official_rc_push_verified"]
          else "GQ8_PR_PREMERGE_8_DOMAIN_SOURCE_ONLY_PASS_NOT_OFFICIAL_RC")
    print("GQ8_OFFICIAL_RC_SHA_PLACE_BYTES",result["official_rc_head"],
          result["studio_place_bytes"],result["studio_place_sha256"])

if __name__=="__main__":
    main()
