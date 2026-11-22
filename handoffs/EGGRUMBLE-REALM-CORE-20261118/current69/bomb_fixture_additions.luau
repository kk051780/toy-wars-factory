-- BasePart.CanQuery defaults to true in Roblox. The reused melee-only fixture
-- previously queried RespectCanCollide and therefore omitted this property.
-- BOMB's unchanged downward ray uses CanQuery, so model this API default.
for _,part in ipairs(workspace:GetDescendants())do
 if part:IsA('BasePart') and part._props.CanQuery==nil then part._props.CanQuery=true end
end
local bombFixtureNew=Instance.new
Instance.new=function(class)
 local item=bombFixtureNew(class)
 if item:IsA('BasePart')then item._props.CanQuery=true end
 return item
end
