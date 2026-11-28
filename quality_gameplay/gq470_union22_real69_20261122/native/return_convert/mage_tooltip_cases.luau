do
local spells={
 {"火種","中立1体｜射程8–16｜E30"},
 {"霜弾","中立1体｜射程8–16｜E30"},
 {"氷槍","中立1–3体｜射程9–17｜E35"},
 {"雷針","中立1体｜射程9–17｜E35"},
}
local function actualTooltip(index)
 local stand=scenes:FindFirstChild("ROLE_MAGE")
 trigger(player,stand,"職業選択")
 for _=1,index do
  advanceTo(now+1.01)
  trigger(player,stand,"属性を装備")
 end
 ready("PRIVATE_FIXED_TOOL_READOUT_"..index)
 for _,tool in ipairs(player:FindFirstChildOfClass("Backpack"):GetChildren()) do
  if tool:IsA("Tool") and tool.Name=="技A・"..spells[index][1] then
   check(string.find(tool.ToolTip,spells[index][2],1,true)~=nil,tool.ToolTip)
   return "actual equipped Tool tooltip matches the same recipe limits and energy"
  end
 end
 error("expected actual equipped Tool: "..spells[index][1])
end
for index=1,#spells do
 growthCases["element_tooltip_"..index]=function() return actualTooltip(index) end
end
end
