local beforeDeferredInstance=Instance.new
Instance.new=function(class)
 local object=beforeDeferredInstance(class)
 object._props.AncestryChanged=signal()
 return object
end
local beforeDeferredWrite=instanceMeta.__newindex
instanceMeta.__newindex=function(self,key,value)
 local previous=self._props[key]
 beforeDeferredWrite(self,key,value)
 if key=='Parent' and previous~=value then
  local own=self._props.AncestryChanged
  if own then own:Fire(self,value)end
  -- Descendant notifications share the original changed ancestor and new parent.
  for _,descendant in ipairs(self:GetDescendants())do
   local related=descendant._props.AncestryChanged
   if related then related:Fire(self,value)end
  end
 end
end
