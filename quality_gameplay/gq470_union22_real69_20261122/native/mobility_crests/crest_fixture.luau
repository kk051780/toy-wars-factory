
-- Native dependency injection only. Roblox provides these properties/signals.
function methods:GetPropertyChangedSignal(name)
 local existing=self._props.crestFixtureSignals
 if not existing then existing={};self._props.crestFixtureSignals=existing end
 if not existing[name] then existing[name]=signal() end
 return existing[name]
end
local previousCrestFixtureWrite=instanceMeta.__newindex
instanceMeta.__newindex=function(self,key,value)
 local before=self._props[key]
 previousCrestFixtureWrite(self,key,value)
 local existing=self._props.crestFixtureSignals
 if existing and existing[key] and before~=value then existing[key]:Fire() end
end
local previousCrestFixtureNew=Instance.new
Instance.new=function(class)
 local obj=previousCrestFixtureNew(class)
 if class=="Camera" then obj._props.CameraType=Enum.CameraType.Scriptable end
 return obj
end
allowedNil.CameraSubject=true
