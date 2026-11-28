function growthCases.transform_switch_kits()
 local stand=scenes:FindFirstChild("ROLE_BUILDER")
 trigger(player,stand,"職業選択")
 trigger(player,stand,"変形を装備")
 check(player:GetAttribute("EGGRUMBLE_LobbyBuilderLoadoutName")=="超機変形・超機磁甲","new J has its explicit optional gear")
 trigger(player,stand,"遮蔽を装備")
 check(player:GetAttribute("EGGRUMBLE_LobbyBuilderLoadoutName")=="盾機","old G clears J and retains its shield")
 advanceTo(now+.51)
 trigger(player,stand,"変形を装備")
 check(player:GetAttribute("EGGRUMBLE_LobbyBuilderLoadoutName")=="超機変形・超機磁甲","J remains reversible")
 trigger(player,stand,"装備する")
 workspace:SetAttribute("P0D_ENABLE_PRIVATE_BUILDER_TRANSFORM",false)
 drainDeferred()
 check(player:GetAttribute("EGGRUMBLE_LobbyBuilderLoadoutName")=="連装砲・星環飛行艇・星環空砲","old F remains selected when only J is disabled")
 local live=ready("PRIVATE_BUILDER_TRANSFORM_KITS","BUILDER")
 local oldCombo=false
 for _,item in ipairs(player:FindFirstChildOfClass("Backpack"):GetChildren()) do
  if item:GetAttribute("EGGRUMBLE_FixedAbilityId")=="COMBO-013" then oldCombo=true end
 end
 check(live.builderFlightLoadouts[player.UserId]==true and not live.builderTransformLoadouts[player.UserId] and oldCombo,
  "existing Host and Tool mount the actual old cannon/flight deck after the new mode is OFF")
 return "new J, old G and old F switch cleanly, and real legacy F Tools survive the independent OFF"
end
