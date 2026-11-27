local cases={
 {"WARRIOR","武神","大太刀"},
 {"MAGE","魔法使い","魔法弾"},
 {"NINJA","暗殺者","双刃"},
 {"TRAPPER","超能力者","念動球"},
 {"BUILDER","マッドサイエンティスト","砲塔"},
 {"BEAST","魔獣使い","魔獣召喚"},
 {"ZOMBIE","呪術師","呪印"},
}
for _,row in ipairs(cases) do
 player.attrs={EGGRUMBLE_SelectedRole=row[1]}
 local intro=cue(0)
 assert(string.find(intro,row[2],1,true) and string.find(intro,row[3],1,true)
  and string.find(intro,"モード選択",1,true),row[1])
 for line in string.gmatch(intro,"[^\n]+") do
  assert(utf8.len(line)<=15,"two-line existing box: "..row[1])
 end
end
print("FB004_EACH_REAL_ROLE_HAS_OWN_FIRST_ACTION_PASS")

player.attrs={EGGRUMBLE_SelectedRole="MAGE",EGGRUMBLE_LobbyMageProjectileName="霜弾"}
assert(cue(0)=="霜弾\nモードを選んで出撃")
player.attrs={EGGRUMBLE_SelectedRole="BEAST",EGGRUMBLE_LobbyBeastLoadoutName="雷角竜"}
assert(cue(0)=="雷角竜\nモードを選んで出撃")
player.attrs={EGGRUMBLE_SelectedRole="NINJA",EGGRUMBLE_LobbyNinjaLoadoutName="瞬歩・煙玉・霞瞬歩"}
assert(string.find(cue(0),"霞瞬歩",1,true))
workspace.attrs.P0D_ENABLE_PRIVATE_NINJA_COMBO_008=false
assert(string.find(cue(0),"双刃",1,true))
player.attrs.EGGRUMBLE_LobbyNinjaLoadoutName=nil
player.attrs.EGGRUMBLE_SelectedRole="BUILDER"
player.attrs.EGGRUMBLE_LobbyBuilderLoadoutName=string.rep("星",20)
assert(cue(0)=="マッドサイエンティスト\n装備済み｜モード選択")
print("FB004_KIT_SELECTION_SAFE_ROLLBACK_AND_NARROW_FALLBACK_PASS")

player.attrs={EGGRUMBLE_SelectedRole="MAGE",EGGRUMBLE_QueuedMode="TEAM"}
assert(cue(12)=="1/3  チーム戦の開始を待とう" and deployedAt==nil)
player.attrs.EGGRUMBLE_QueuedMode="BATTLE_ROYALE"
assert(cue(14)=="1/3  全員対戦の開始を待とう" and deployedAt==nil)
player.attrs.EGGRUMBLE_Role="MAGE"
assert(cue(20)=="［攻撃／技A］で攻撃\n［技］で固有技を選ぶ" and deployedAt==20)
assert(cue(42)=="2/3  卵を奪う／敵の城を攻める")
assert(cue(68)=="3/3  卵を運び帰ろう")
player.attrs.EGGRUMBLE_Eliminated=true
assert(cue(69)=="" and deployedAt==nil)
player.attrs={EGGRUMBLE_SelectedRole="FAKE"}
assert(cue(70)=="1/3  役職と対戦モードを選ぼう")
print("FB004_READY_COMBAT_BUTTONS_OBJECTIVE_AND_ELIMINATION_PASS")
