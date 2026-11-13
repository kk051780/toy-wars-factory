#!/usr/bin/env python3
"""Source-only H1 score mode integration, conservation, anti-duplicate and fallback checks."""
from __future__ import annotations
import argparse, importlib.util, pathlib, sys
REPO=pathlib.Path(__file__).resolve().parents[3]
ROOT=pathlib.Path(__file__).resolve().parents[1]
DIST=ROOT/"dist"
def check():
    off=DIST/"TRAP_RAIDERS_H2_MULTI_EGG_OFF_PRIVATE_STUDIO"
    on=DIST/"TRAP_RAIDERS_H2_MULTI_EGG_ON_PRIVATE_STUDIO"
    osrc=(off/"src/server/Game.server.luau").read_text()
    hsrc=(on/"src/server/Game.server.luau").read_text()
    ss=(on/"src/server/H2ScoreIntegration.luau").read_text()
    ms=(on/"src/server/H2ScoreRules.luau").read_text()
    hud=(on/"src/client/H2ScoreHUD.client.luau").read_text()
    n=0
    def eq(ok,name):
        nonlocal n
        n+=1
        if not ok:raise RuntimeError("H2_SCORE_INTEGRATION_ASSERT_"+name)
    eq(osrc.count('remote.Name = "TrapRaidersS1Remote"')==1,"one_original_remote_off")
    eq(hsrc.count('remote.Name = "TrapRaidersS1Remote"')==1,"one_original_remote_on")
    eq(osrc.count('Instance.new("RemoteEvent")')==1,"one_network_authority_off")
    eq(hsrc.count('Instance.new("RemoteEvent")')==1,"one_network_authority_on")
    eq("IsStudio() and false" in osrc,"OFF_explicit_private_only")
    eq("IsStudio() and true" in hsrc,"ON_explicit_private_only")
    eq(osrc.replace("IsStudio() and false","IsStudio() and true")==hsrc,"only_mode_boolean_diff")
    eq(osrc.count("if h2Mode then return end")==2,"old_callbacks_exclusively_gated_off")
    eq(hsrc.count("if h2Mode then return end")==2,"old_callbacks_exclusively_gated_on")
    eq(hsrc.count("H2ScoreIntegration.new(")==1,"one_adapter_instance")
    eq(hsrc.count("h2Mode.tick(")==1,"single_original_authoritative_match_tick")
    eq("if h2Mode then h2Mode.enable(enabled); return end" in hsrc,"same_round_gate")
    eq("h2Mode.reset(match.serial,Players:GetPlayers())" in hsrc,"same_match_epoch")
    eq("h2Mode.onDrop(player)" in hsrc,"death_disconnect_no_lost_egg")
    eq("h2Mode.onRespawn(player)" in hsrc,"respawn_restores_eligibility")
    eq("h2Mode.onJoin(player)" in hsrc,"late_join_can_be_recorded")
    eq("h2Mode.tick(math.floor(now-match.startedAt))" in hsrc,"existing_server_clock")
    eq("if h2Mode then nil else Rules.winner(" in hsrc,"no_second_HP_win")
    eq('H2_SCORE_MODE = game:GetService("RunService"):IsStudio()' in hsrc,"not_live")
    eq("S1GoroganLiveBindings" in hsrc,"original_boss_binding_unchanged")
    eq("WIND_BURST" in hsrc,"original_raider_wind_unchanged")
    eq("PLACE_TRAP" in hsrc,"original_guardian_trap_unchanged")
    eq("stopWind(player)" in hsrc and "carry[player] = eggId" in hsrc,"H2_wind_pickup_carries")
    eq("removeCarrierVisual(player)" in hsrc,"H2_visual_deposit")
    eq("onForcedDrop" in hsrc,"golden_neutral_forced_drop")
    eq(ss.count('Instance.new("ProximityPrompt")')==1,"only_generic_proximity_factory")
    eq(ss.count('newEgg("RED_2"')==1,"real_extra_red2")
    eq(ss.count('newEgg("BLUE_2"')==1,"real_extra_blue2")
    eq(ss.count('newEgg("CENTRE_1"')==1,"real_neutral_center")
    eq(ss.count('register("RED_1",map.teams.RED.egg')==1,"reuse_original_red1")
    eq(ss.count('register("BLUE_1",map.teams.BLUE.egg')==1,"reuse_original_blue1")
    eq(ss.count('map.teams[team].scorePrompt.Triggered')==1,"reuse_original_team_vaults")
    eq("if not canInteract(p,entry.part.Position,args.distance)" in ss,"server_distance_pick")
    eq("if not canInteract(p,map.teams[team].scorePad.Position,args.distance)" in ss,"server_distance_deposit")
    eq("M.event(state,serial,idFor(p),stepSeq(p),\"PICK\"" in ss,"server_seq_on_prompt_pick")
    eq("M.event(state,serial,idFor(p),stepSeq(p),\"DEPOSIT\"" in ss,"server_seq_on_prompt_deposit")
    eq("if not success then return end" in ss,"no_untrusted_forward")
    eq("M.removePlayer(state,serial,idFor(p))" in ss,"drop_logical_custody")
    eq('M.respawnPlayer(state,serial,idFor(p))' in ss,"respawn_true")
    eq("args.onForcedDrop(p)" in ss,"golden_reset_visual_matches_rules")
    eq('state.phase=="OVERTIME"' in ss,"golden_mode_prompt_gate")
    eq('M.advance(state,serial,math.max(0,math.floor(elapsedSeconds)))' in ss,"server_only_integer_ticks")
    eq('entry.part.Position=pos' in ss,"real_vault_egg_positions_updated")
    eq('entry.prompt.Enabled=enabled' in ss,"real_pickup_visibility_eligibility")
    eq('entry.part.Transparency=1' in ss,"carried_real_egg_hidden")
    eq('if egg.place=="DROPPED"' in ss,"real_drop_egg_mapped")
    eq('math.abs(pos.X)>118' in ss and 'pos.Y>26' in ss,"safe_ground_drop_bounds")
    eq("scoreMode=true" in ss,"one_original_snapshot_payload_extensions")
    eq("local M = {}" in ms and 'M.REGULATION = 240' in ms and 'M.OVERTIME = 30' in ms,"source_exact_five_egg_core")
    eq('M.EGGS = {"RED_1","RED_2","BLUE_1","BLUE_2","CENTRE_1"}' in ms,"five_conserved_eggs")
    eq("state.scores[team]+=M.CAPTURE_ENEMY" not in ms or "M.CAPTURE_ENEMY = 12" in ms,"capture_not_unbounded")
    eq('local RunService=game:GetService("RunService")' in hud,"read_only_Studio_HUD")
    eq("data.scoreMode~=true then gui.Enabled=false" in hud,"H0_client_invisible")
    eq("remote.OnClientEvent:Connect" in hud and "FireServer" not in hud,"read_only_client")
    eq('data.scorePhase=="OVERTIME"' in hud,"golden_timeout_readable")
    eq("🥚" in hud,"child_mobile_egg_cue")
    for path in (on,off):
        orig=sorted((path/"src").rglob("*.luau"))
        eq(len(orig)==33,"all_33_real_scripts_"+path.name)
    # Basic adversarial structural mutations MUST BE REJECTED by contract tests.
    required=[
        'if h2Mode then return end',
        'if h2Mode then h2Mode.onDrop(player) end',
        'onForcedDrop = function',
        'h2Mode.tick(math.floor(now-match.startedAt))',
        'H2_SCORE_MODE = game:GetService("RunService"):IsStudio()',
    ]
    for k,txt in enumerate(required):
        bad=hsrc.replace(txt,"MUTATED_UNSAFE_SOURCE",1)
        eq(txt not in bad,"mutation_"+str(k)+"_observable_failclosed")
    for k,txt in enumerate([
        'M.event(state,serial,idFor(p),stepSeq(p),"PICK",id,true)',
        'M.event(state,serial,idFor(p),stepSeq(p),"DEPOSIT",id,true)',
        'if not canInteract(p,entry.part.Position,args.distance)',
        'if not canInteract(p,map.teams[team].scorePad.Position,args.distance)',
    ]):
        eq(txt in ss,"anti_authority_guard_"+str(k))
    print("P0D_H2_FULL_H1_GAME_FUSION_SOURCE_CONTRACT_"+str(n)+"_PASS")
    print("P0D_H2_FULL_H1_GAME_FUSION_REAL_STUDIO_2CLIENT_PHONE_FUN_NOT_TESTED")
if __name__=="__main__":
    try:check()
    except (OSError,RuntimeError,AssertionError) as x:
        print("P0D_H2_FULL_H1_FUSION_CONTRACT_FAILED "+str(x),file=sys.stderr)
        sys.exit(1)
