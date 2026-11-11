"""Build native Luau runtime tests from EXACT original WF13 controller and policy.
Mocks Roblox services only. Original Luau body is unchanged except require redirection.
Produces 1 valid runner + 2 intentionally corrupted controller runners.
"""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "src/WF13Policy.luau"
CONTROL = ROOT / "src/WF13ZoneController.luau"

MOCKS_AND_CASES = r'''
local function V(x,y,z)
    return setmetatable({X=x,Y=y,Z=z}, {
        __add = function(a,b) return V(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
    })
end
Vector3 = {new=V,zero=V(0,0,0)}
CFrame = {new = function(position)
    if type(position) == "number" then return {Position=V(position,0,0)} end
    return {Position=position}
end}
Enum = {ActuatorRelativeTo={World="World"}}

Instance = {new = function(kind)
    local o={ClassName=kind,Name=kind,Parent=nil,Enabled=true}
    function o:Destroy() self.Parent=nil; self.destroyed=true end
    return o
end}
local function Event()
    local o={_callbacks={}}
    function o:Connect(callback)
        table.insert(self._callbacks,callback)
        local connection={Connected=true}
        function connection:Disconnect() self.Connected=false end
        self._callbacks[#self._callbacks].connection=connection
        return connection
    end
    function o:Fire(...)
        for _,callback in ipairs(self._callbacks) do callback(...) end
    end
    return o
end

local count=0
local function ok(condition, message)
    count+=1
    assert(condition,"WF13_NATIVE_CONTROLLER_FAILED #"..tostring(count)..": "..message)
end

local workspace={Gravity=196.2}
local zone={Parent=workspace, Size=V(82,58,82), Position=V(0,27,0)}
function zone:IsA(name) return name=="BasePart" end
function zone:IsDescendantOf(other) return other==workspace end
zone.CFrame={PointToObjectSpace=function(self,p)
    return V(p.X-zone.Position.X,p.Y-zone.Position.Y,p.Z-zone.Position.Z)
end}
local safe={Parent=workspace,Position=V(-58,1,0)}
function safe:IsA(name) return name=="BasePart" end
local root={Parent={},Position=V(100,27,0),Anchored=false,AssemblyMass=100,
    AssemblyLinearVelocity=V(0,0,0),attrs={},auto=true,netOwner=nil}
function root:IsA(class) return class=="BasePart" end
function root:FindFirstChild(name) return nil end
function root:GetAttribute(name) return self.attrs[name] end
function root:SetAttribute(name,value) self.attrs[name]=value end
function root:CanSetNetworkOwnership() return true end
function root:GetNetworkOwnershipAuto() return self.auto end
function root:GetNetworkOwner() return self.netOwner end
function root:SetNetworkOwner(owner) self.netOwner=owner;self.auto=false end
function root:SetNetworkOwnershipAuto() self.netOwner=nil;self.auto=true end
local human={Health=100}
local char={Parent={},Name="FakeCharacter"}
function char:FindFirstChild(name)
    if name=="HumanoidRootPart" then return root end
    return nil
end
function char:FindFirstChildOfClass(name)
    if name=="Humanoid" then return human end
    return nil
end
function char:PivotTo(cf)
    root.Position=cf.Position
end
local p={Parent={},Character=char,CharacterRemoving=Event()}
local players={roster={p},PlayerAdded=Event(),PlayerRemoving=Event()}
function players:GetPlayers() return self.roster end
local heartbeat=Event()
local runService={Heartbeat=heartbeat}
local ctrl=Controller.new({
    players=players,runService=runService,workspace=workspace,zone=zone,safePad=safe
})
ctrl:start()
ok(ctrl.running,"controller starts")
ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p]==nil,"no force outside region")
ok(root.auto and root.netOwner==nil,"network ownership unchanged outside")

root.Position=V(0,27,0)
ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p]~=nil,"entered actual zone")
ok(root:GetAttribute("WF13GravityOwner")~=nil,"exclusive token")
ok(root.auto==false,"server took physics ownership")
ok(root.netOwner==nil,"server owner never another player")
ok(ctrl.records[p].force.Parent==root,"force parented to root")
ok(ctrl.records[p].attachment.Parent==root,"attachment parented to root")
ok(ctrl.records[p].force.Force.Y>10000,"force correct order of magnitude")
ok(workspace.Gravity==196.2,"global gravity remains unchanged")
ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p].dwell>0.08,"dwell increments only inside")

local second=Controller.new({players=players,runService=runService,
    workspace=workspace,zone=zone,safePad=safe})
second:_samplePlayer(p,0.08)
ok(second.records[p]==nil,"second controller refuses existing owner")

root.AssemblyLinearVelocity=V(90,100,0)
ctrl:_samplePlayer(p,0.08)
ok(root.AssemblyLinearVelocity.X==48 and root.AssemblyLinearVelocity.Y==30,
   "fast fly speed restricted")

root.Position=V(90,27,0)
ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p].mode=="landing","exit starts controlled fade")
ctrl:_samplePlayer(p,1)
ctrl:_samplePlayer(p,1.05)
ok(ctrl.records[p]==nil,"fade cleans force")
ok(root.auto and root.netOwner==nil,"original auto owner restored")
ok(root:GetAttribute("WF13GravityOwner")==nil,"owner attribute removed")

root.Position=V(0,27,0)
ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p]~=nil,"re-entry allowed after leaving")

-- Hardening: an unrelated long-range teleport outside the sphere must NOT snap back.
root.Position=V(900,-120,900)
ctrl:_samplePlayer(p,0.08)
ok(root.Position.X==900 and root.Position.Z==900,"far teleport not pulled to safe pad")
ok(ctrl.records[p].mode=="landing","teleport transitions to landing")
ctrl:_samplePlayer(p,2.1)
ok(ctrl.records[p]==nil,"teleport cleanup completed")

root.Position=V(0,27,0)
ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p]~=nil,"reenter after teleport")
root.Position=V(0,-100,0)
ctrl:_samplePlayer(p,0.08)
ok(root.Position.X==-58 and root.Position.Y==6,"near-zone deep fall rescued")

root.Position=V(0,27,0)
ctrl:_samplePlayer(p,0.08)
local oldEntry=ctrl.records[p]
oldEntry.attachment.Parent=nil
ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p]==nil,"broken attachment forces cleanup")
ok(ctrl.blockedUntilExit[p]==true,"invalid attachment blocks reenter while still inside")
ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p]==nil,"blocked reentry remains blocked")
root.Position=V(90,27,0)
ctrl:_samplePlayer(p,0.08)
ok(ctrl.blockedUntilExit[p]==nil,"leaving resets blocked flag")

root.Position=V(0,27,0)
ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p]~=nil,"reentry after valid exit")
human.Health=0
ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p]==nil,"death immediately clears force")
ok(root.auto,"death restores ownership")
human.Health=100

ctrl:_samplePlayer(p,0.08)
ok(ctrl.records[p]~=nil,"reenter after death")
players.PlayerRemoving:Fire(p)
ok(ctrl.records[p]==nil,"player leaving clears force")
ok(ctrl.blockedUntilExit[p]==nil,"player leaving clears guard")
ctrl:stop()
ok(ctrl.running==false and ctrl.destroyed==true,"stop finalizes")
ok(root.auto and root:GetAttribute("WF13GravityOwner")==nil,"shutdown leaves no physics authority")
ok(workspace.Gravity==196.2,"world gravity never mutated")
print("WF13_NATIVE_ACTUAL_CONTROLLER_PASS cases="..tostring(count))
'''

def replace_import(source):
    required = "local Policy = require(script.Parent.WF13Policy)"
    if source.count(required) != 1:
        raise ValueError("refuse unfamiliar WF13 Controller source")
    return source.replace(required, "local Policy = WF13_POLICY", 1)

def generate(policy, controller):
    policy=policy.replace("--!strict\n","",1)
    controller=controller.replace("--!strict\n","",1)
    return ("local WF13_POLICY=(function()\n" + policy + "\nend)()\n"
            + "local Controller=(function()\n" + replace_import(controller)
            + "\nend)()\n" + MOCKS_AND_CASES)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True)
    a=parser.parse_args()
    out=Path(a.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    policy=POLICY.read_text(encoding="utf-8")
    controller=CONTROL.read_text(encoding="utf-8")
    variants={
        "positive":controller,
        "BAD_CLIENT_NETWORK_OWNER": controller.replace(
            "root:SetNetworkOwner(nil)", "root:SetNetworkOwner(player)", 1),
        "BAD_NO_REAL_REGION_CHECK": controller.replace(
            "return Policy.insideEllipsoid(localPos.X, localPos.Y, localPos.Z, size.X, size.Y, size.Z)",
            "return true", 1),
    }
    if len({v for v in variants.values()}) != 3:
        raise RuntimeError("negative mutations didn't change real code")
    for name, source in variants.items():
        path=out/(name+".luau")
        path.write_text(generate(policy,source),encoding="utf-8")
        print("WF13_NATIVE_REAL_CONTROLLER_RUNNER_WRITTEN",name,path)
if __name__=="__main__":
    main()
