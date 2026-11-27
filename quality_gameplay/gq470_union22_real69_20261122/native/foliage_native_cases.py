"""Run the selected A01 LocalScript through a deterministic Native Luau fixture."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


QA = Path(__file__).resolve().parents[1] / "gq470-art-quality-20261121"
ROUTE = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD.client.luau"
OFFICIAL_SHA = "565a9e2e4e3ee794636116d802c887f799c685a7bedb5cf72d30a130165b147d"
ART17_SHA = "30c8c5c1946cef9d3ee194f70e2770b08f54e6ba91282b9d2048031eeb4b306a"

MOCKS = r'''
local vector = {}
local Vector3 = {}
function Vector3.new(x,y,z)
    return setmetatable({X=x,Y=y,Z=z}, vector)
end
Vector3.zero = Vector3.new(0,0,0)
function vector:Dot(other) return self.X*other.X+self.Y*other.Y+self.Z*other.Z end
function vector.__index(value,key)
    if key == "Magnitude" then return math.sqrt(value:Dot(value)) end
    if key == "Unit" then return value/value.Magnitude end
    return vector[key]
end
function vector.__add(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
function vector.__sub(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
function vector.__mul(a,k) return Vector3.new(a.X*k,a.Y*k,a.Z*k) end
function vector.__div(a,k) return a*(1/k) end

local function frame(position,yaw)
    local c,s = math.cos(yaw or 0), math.sin(yaw or 0)
    local cf = {Position=position}
    function cf:VectorToObjectSpace(v) return Vector3.new(c*v.X-s*v.Z,v.Y,s*v.X+c*v.Z) end
    function cf:VectorToWorldSpace(v) return Vector3.new(c*v.X+s*v.Z,v.Y,-s*v.X+c*v.Z) end
    function cf:PointToObjectSpace(v) return self:VectorToObjectSpace(v-self.Position) end
    function cf:PointToWorldSpace(v) return self.Position+self:VectorToWorldSpace(v) end
    return cf
end

local function signal()
    local callbacks = {}
    local event = {}
    function event:Connect(fn)
        local connection = {Connected=true}
        function connection:Disconnect() self.Connected=false end
        table.insert(callbacks,{connection,fn})
        return connection
    end
    function event:Count()
        local count=0
        for _,entry in ipairs(callbacks) do
            if entry[1].Connected then count+=1 end
        end
        return count
    end
    function event:Fire(...)
        for _,entry in ipairs(table.clone(callbacks)) do
            if entry[1].Connected then entry[2](...) end
        end
    end
    return event
end

local function entity(class,name,parent)
    local props={Name=name,Parent=parent,LocalTransparencyModifier=0,ChildAdded=signal(),AncestryChanged=signal()}
    local object={props=props,writes={}}
    function object:IsA(kind)
        return kind==class or (kind=="BasePart" and (class=="Part" or class=="WedgePart"))
    end
    function object:IsDescendantOf(root)
        local ancestor=props.Parent
        while ancestor do
            if ancestor==root then return true end
            ancestor=ancestor.Parent
        end
        return false
    end
    return setmetatable(object,{
        __index=props,
        __newindex=function(self,key,value)
            assert(key=="LocalTransparencyModifier","unexpected A01 instance write: "..key)
            table.insert(self.writes,value)
            props[key]=value
        end,
    })
end

local function fixture(mobile,isStudio)
    local world={DescendantAdded=signal(),DescendantRemoving=signal()}
    local run={RenderStepped=signal(),Heartbeat=signal()}
    local scriptMock={Parent={},Destroying=signal()}
    local player={}
    local now, serial, nextFrame, frameStep=0,0,.04,.04
    local queued, instances={},{}

    local function enqueue(thread,due)
        serial+=1
        table.insert(queued,{thread=thread,due=due,serial=serial})
    end
    local function resume(thread)
        local ok,delay=coroutine.resume(thread)
        assert(ok,tostring(delay))
        if coroutine.status(thread)~="dead" then
            assert(type(delay)=="number" and delay>0,"expected a positive task.wait delay")
            enqueue(thread,now+delay)
        end
    end
    local function advance(stop)
        assert(stop>=now,"mock time cannot move backwards")
        while true do
            table.sort(queued,function(a,b) return a.due<b.due or (a.due==b.due and a.serial<b.serial) end)
            local timer=queued[1]
            if nextFrame<=stop and (not timer or nextFrame<timer.due) then
                now=nextFrame
                nextFrame+=frameStep
                run.RenderStepped:Fire(frameStep)
                run.Heartbeat:Fire(frameStep)
            elseif timer and timer.due<=stop then
                table.remove(queued,1)
                now=timer.due
                resume(timer.thread)
            else
                now=stop
                break
            end
        end
    end

    local owned=entity("Folder","EGGRUMBLE_FlagshipLandscape_VisualOnly",world)
    local outside=entity("Folder","DifferentOwner",world)
    function world:GetDescendants()
        local result={owned,outside}
        for _,part in ipairs(instances) do
            if part:IsDescendantOf(world) then table.insert(result,part) end
        end
        return result
    end
    function run:IsStudio() return isStudio~=false end
    local services={RunService=run,Players={LocalPlayer=player},UserInputService={TouchEnabled=mobile~=false}}
    local game={GetService=function(_,name) return assert(services[name],"unexpected service "..name) end}
    local task={
        spawn=function(fn) resume(coroutine.create(fn)) end,
        wait=function(seconds) coroutine.yield(seconds) end,
        defer=function(fn,...) local args=table.pack(...); enqueue(coroutine.create(function()
            fn(table.unpack(args,1,args.n))
        end),now) end,
    }
    local enum={PartType={Wedge="Wedge",Block="Block",Ball="Ball"}}
    local result={world=world,owned=owned,outside=outside,run=run,script=scriptMock,advance=advance}
    function result.start() install(game,world,scriptMock,task,Vector3,enum) end
    function result.part(class,name,parent,position,size,yaw,alpha)
        local part=entity(class,name,parent)
        part.props.Position=position
        part.props.CFrame=frame(position,yaw)
        part.props.Size=size
        part.props.Shape=if class=="WedgePart" then enum.PartType.Wedge else enum.PartType.Block
        part.props.LocalTransparencyModifier=alpha or 0
        part.props.SurfaceCalls=0
        part.props.RiseSign=1
        rawset(part,"GetClosestPointOnSurface",function(self,point)
            self.props.SurfaceCalls+=1
            assert(not self.props.SurfaceUnavailable,"closest point API unavailable")
            -- Calibration queries hit the interior of the two triangles in
            -- this section, away from edges. Above-slope queries project to
            -- the ramp. These fixtures do not model unrelated surface APIs.
            local at=self.CFrame:PointToObjectSpace(point)
            local slope=self.props.RiseSign*self.Size.Y/self.Size.Z
            local margin=at.Y-slope*at.Z
            if margin<=0 then return point end
            local step=margin/(1+slope*slope)
            return self.CFrame:PointToWorldSpace(Vector3.new(at.X,at.Y-step,at.Z+slope*step))
        end)
        table.insert(instances,part)
        return part
    end
    function result.canopy(rise)
        -- This is the first layer's actual class and dimensions. A nonzero yaw
        -- exercises the same world-to-object transform as the authored trees.
        local leaf=result.part("WedgePart","ART_Canopy1_1",owned,Vector3.new(11,7,-15),
            Vector3.new(8.7,5.6,8.7),math.rad(98))
        leaf.props.RiseSign=rise or 1
        return leaf
    end
    function result.camera(position)
        world.CurrentCamera=if position then {CFrame=frame(position)} else nil
    end
    function result.avatar(position)
        if not position then player.Character=nil; return end
        local root=entity("Part","HumanoidRootPart",world)
        root.props.Position=position
        player.Character={FindFirstChild=function(_,name) return if name=="HumanoidRootPart" then root else nil end}
    end
    function result.sight(part,eye,avatar)
        result.camera(part.CFrame:PointToWorldSpace(eye))
        result.avatar(if avatar then part.CFrame:PointToWorldSpace(avatar) else nil)
    end
    function result.remove(part,deferred)
        if deferred then
            part.props.Parent=nil
            task.defer(function() world.DescendantRemoving:Fire(part) end)
            advance(now)
        else
            world.DescendantRemoving:Fire(part)
            part.props.Parent=nil
        end
    end
    function result.attach(part,parent)
        part.props.Parent=parent
        world.DescendantAdded:Fire(part)
    end
    return result
end
'''

CASES = r'''
local expectedWedgeGaps = {
    wedge_void_segment="wanted alpha 0.00, got 0.76",
    wedge_void_camera="wanted alpha 0.00, got 0.88",
    wedge_mirrored_calibration="wanted alpha 0.00, got 0.76",
}
local expectedFailures = {
    official={
        rotated_blocker="wanted alpha 0.76, got 0.93",
        near_side_miss="wanted alpha 0.00, got 0.93",
        inside_canopy="wanted alpha 0.88, got 0.93",
        behind_avatar="wanted alpha 0.00, got 0.93",
        bounded_scheduled_pass="unexpected per-frame listener",
        deferred_detach_restores="wanted alpha 0.00, got 0.93",
        wedge_void_segment="wanted alpha 0.00, got 0.93",
        wedge_void_camera="wanted alpha 0.00, got 0.93",
        wedge_mirrored_calibration="wanted alpha 0.76, got 0.93",
    },
    art17=table.clone(expectedWedgeGaps),
    candidate=if requireWedge then {} else expectedWedgeGaps,
}
expectedFailures.art17.deferred_detach_restores="wanted alpha 0.00, got 0.76"
local passed, expected, failed=0,0,0
local function check(name,fn)
    local ok,message=pcall(fn)
    local wantedMessage=expectedFailures[profile][name]
    if wantedMessage then
        if ok then
            failed+=1
            print("UNEXPECTED_PASS\t"..name)
        elseif not string.find(tostring(message),wantedMessage,1,true) then
            failed+=1
            print("UNEXPECTED_FAILURE\t"..name.."\t"..tostring(message))
        else
            expected+=1
            print("REPRODUCED\t"..name.."\t"..tostring(message))
        end
    elseif ok then
        passed+=1
        print("PASS\t"..name)
    else
        failed+=1
        print("FAIL\t"..name.."\t"..tostring(message))
    end
end

local function alpha(part,want)
    local got=part.LocalTransparencyModifier
    assert(math.abs(got-want)<1e-6,("wanted alpha %.2f, got %.2f"):format(want,got))
end

check("rotated_blocker",function()
    local scene=fixture()
    local leaf=scene.canopy()
    scene.sight(leaf,Vector3.new(-12,-2,0),Vector3.new(12,-2,0))
    scene.start()
    scene.advance(.18)
    alpha(leaf,.76)
end)

check("near_side_miss",function()
    local scene=fixture()
    local leaf=scene.canopy()
    scene.sight(leaf,Vector3.new(-7,-2,5.1),Vector3.new(8,-2,5.1))
    scene.start()
    scene.advance(.18)
    alpha(leaf,0)
end)

check("inside_canopy",function()
    local scene=fixture()
    local leaf=scene.canopy()
    scene.sight(leaf,Vector3.new(0,-2,0),nil)
    scene.start()
    scene.advance(.18)
    alpha(leaf,.88)
end)

check("behind_avatar",function()
    local scene=fixture()
    local leaf=scene.canopy()
    scene.sight(leaf,Vector3.new(-11,-2,0),Vector3.new(-6,-2,0))
    scene.start()
    scene.advance(.18)
    alpha(leaf,0)
end)

check("bounded_scheduled_pass",function()
    local scene=fixture()
    local leaf=scene.canopy()
    scene.sight(leaf,Vector3.new(-12,-2,0),Vector3.new(12,-2,0))
    scene.start()
    assert(scene.run.RenderStepped:Count()==0 and scene.run.Heartbeat:Count()==0,"unexpected per-frame listener")
    scene.advance(.15)
    alpha(leaf,0)
    scene.advance(.18)
    alpha(leaf,.76)
end)

check("far_dominates_and_near_resyncs",function()
    local scene=fixture()
    local leaf=scene.canopy()
    local blocking=if profile=="official" then .93 else .76
    scene.sight(leaf,Vector3.new(-185,-2,0),Vector3.new(12,-2,0))
    scene.start()
    scene.advance(1.39)
    alpha(leaf,1)
    scene.sight(leaf,Vector3.new(-130,-2,0),Vector3.new(12,-2,0))
    scene.advance(2.60)
    alpha(leaf,1)
    scene.sight(leaf,Vector3.new(-95,-2,0),Vector3.new(12,-2,0))
    scene.advance(3.90)
    alpha(leaf,blocking)
    scene.sight(leaf,Vector3.new(-95,-2,5.1),Vector3.new(12,-2,5.1))
    scene.advance(4.14)
    -- Legacy spherical tolerance intentionally remains visible in the OFF comparison.
    alpha(leaf,if profile=="official" then .93 else 0)
end)

check("only_owned_art_is_touched",function()
    local scene=fixture()
    local leaf=scene.canopy()
    local fx=scene.part("Part","WeaponFX",scene.owned,leaf.Position,leaf.Size,0,.21)
    local other=scene.part("WedgePart","ART_Canopy2_1",scene.outside,leaf.Position,leaf.Size,0,.33)
    scene.sight(leaf,Vector3.new(-185,-2,0),Vector3.new(12,-2,0))
    scene.start()
    scene.advance(1.4)
    alpha(leaf,1)
    alpha(fx,.21)
    alpha(other,.33)
    assert(#fx.writes==0 and #other.writes==0)
end)

check("missing_camera_and_non_studio_start",function()
    local noCamera=fixture()
    local leaf=noCamera.canopy()
    noCamera.start()
    noCamera.advance(1.4)
    alpha(leaf,0)
    assert(#leaf.writes==0)
    local liveGame=fixture(true,false)
    local gameLeaf=liveGame.canopy()
    liveGame.sight(gameLeaf,Vector3.new(-185,-2,0),Vector3.new(12,-2,0))
    liveGame.start()
    liveGame.advance(1.4)
    assert(#gameLeaf.writes==0 and liveGame.world.DescendantAdded:Count()==0)
end)

check("immediate_removal_restores",function()
    local scene=fixture()
    local leaf=scene.canopy()
    scene.sight(leaf,Vector3.new(-12,-2,0),Vector3.new(12,-2,0))
    scene.start()
    scene.advance(.18)
    assert(leaf.LocalTransparencyModifier>0,"fixture failed to fade the canopy")
    scene.remove(leaf,false)
    alpha(leaf,0)
    scene.attach(leaf,scene.outside)
    scene.advance(1.4)
    alpha(leaf,0)
end)

check("deferred_detach_restores",function()
    local scene=fixture()
    local leaf=scene.canopy()
    scene.sight(leaf,Vector3.new(-12,-2,0),Vector3.new(12,-2,0))
    scene.start()
    scene.advance(.18)
    assert(leaf.LocalTransparencyModifier>0,"fixture failed to fade the canopy")
    scene.remove(leaf,true)
    assert(leaf.Parent==nil,"fixture did not deliver after Parent=nil")
    scene.attach(leaf,scene.outside)
    scene.advance(1.4)
    alpha(leaf,0)
end)

check("wedge_void_segment",function()
    local scene=fixture()
    local leaf=scene.canopy()
    -- At local Z=0 the slope meets local Y=0 whichever end is the tall end.
    scene.sight(leaf,Vector3.new(-12,2,0),Vector3.new(12,2,0))
    scene.start()
    scene.advance(.18)
    alpha(leaf,0)
end)

check("wedge_void_camera",function()
    local scene=fixture()
    local leaf=scene.canopy()
    scene.sight(leaf,Vector3.new(0,2,0),nil)
    scene.start()
    scene.advance(.18)
    alpha(leaf,0)
end)

check("wedge_mirrored_calibration",function()
    for _,rise in ipairs({1,-1}) do
        local scene=fixture()
        local leaf=scene.canopy(rise)
        -- These two paths are above the central height. They are in the wedge
        -- toward the tall end and outside it toward the short end.
        scene.sight(leaf,Vector3.new(-12,1,rise*3),Vector3.new(12,1,rise*3))
        scene.start()
        scene.advance(.18)
        alpha(leaf,.76)
        scene.sight(leaf,Vector3.new(-12,1,-rise*3),Vector3.new(12,1,-rise*3))
        scene.advance(.66)
        alpha(leaf,0)
        assert(leaf.SurfaceCalls==2,"wedge orientation should be sampled only at intake")
    end
end)

check("unavailable_closest_point_keeps_conservative_fade",function()
    local scene=fixture()
    local leaf=scene.canopy()
    leaf.props.SurfaceUnavailable=true
    scene.sight(leaf,Vector3.new(-12,2,0),Vector3.new(12,2,0))
    scene.start()
    scene.advance(.18)
    alpha(leaf,if profile=="official" then .93 else .76)
end)

print("SUMMARY\t"..passed.."\t"..expected.."\t"..failed)
assert(failed==0,"native A01 regression failed")
'''


def source_file(path: Path, digest: str | None = None) -> bytes:
    raw = path.read_bytes()
    if digest is not None and hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"Source SHA-256 drifted for {path.name}")
    return raw


def run(luau: Path, source: bytes, profile: str, require_wedge: bool) -> dict:
    header = f'local profile="{profile}"\nlocal requireWedge={str(require_wedge).lower()}'
    payload = b"\n".join((header.encode(), b"local function install(game,workspace,script,task,Vector3,Enum)",
                         source, b"end", MOCKS.encode(), CASES.encode()))
    with tempfile.TemporaryDirectory(prefix="eggrumble-foliage-native-") as folder:
        working = Path(folder)
        fixture = working / "case.luau"
        fixture.write_bytes(payload)
        result = subprocess.run([str(luau.resolve()), fixture.name], cwd=working, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=25, check=False)
    output = result.stdout.splitlines()
    summaries = [line.split("\t")[1:] for line in output if line.startswith("SUMMARY\t")]
    if result.returncode or len(summaries) != 1:
        raise RuntimeError(f"{profile} Native Luau fixture failed\n{result.stdout}{result.stderr}")
    passed, reproduced, problems = map(int, summaries[0])
    return {
        "source_bytes": len(source),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "passed": passed,
        "reproduced_expected_defects": reproduced,
        "unexpected": problems,
        "cases": [line for line in output if line.startswith(("PASS\t", "REPRODUCED\t"))],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", nargs="?", type=Path)
    parser.add_argument("--official", type=Path, default=QA / "baseline" / ROUTE)
    parser.add_argument("--art17", type=Path, default=QA / "composition17" / ROUTE)
    parser.add_argument("--luau", type=Path, default=QA / "toolchain/luau-f46d879/luau.exe")
    parser.add_argument("--require-wedge", action="store_true", help="Require the candidate to preserve opaque void space above the wedge slope")
    args = parser.parse_args()
    report = {
        "runtime": "Native Luau executing the full selected LocalScript with simulated Roblox events and geometry",
        "studio": "NOT_TESTED",
        "official": run(args.luau, source_file(args.official, OFFICIAL_SHA), "official", False),
        "art17": run(args.luau, source_file(args.art17, ART17_SHA), "art17", False),
    }
    if args.candidate:
        report["candidate"] = run(args.luau, source_file(args.candidate), "candidate", args.require_wedge)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
