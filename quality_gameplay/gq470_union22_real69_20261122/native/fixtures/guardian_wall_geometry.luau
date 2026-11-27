-- Additional Native fixture capability for Guardian block casts.
-- This fixture already approximates every BasePart as an axis-aligned box.
do
    local originalFrame=CFrame.new
    local function translated(frame,delta)
        local nextFrame=table.clone(frame)
        nextFrame.Position=frame.Position+delta
        return setmetatable(nextFrame,getmetatable(frame))
    end
    CFrame.new=function(...)
        local frame=originalFrame(...)
        local original=getmetatable(frame)
        if original and original.__add then return frame end
        local extended=if original then table.clone(original) else {}
        extended.__add=translated
        return setmetatable(frame,extended)
    end
    local axes={"X","Y","Z"}
    local normals={X=Vector3.new(1,0,0),Y=Vector3.new(0,1,0),Z=Vector3.new(0,0,1)}
    workspace.Blockcast=function(_,frame,size,delta,params)
        assert(params.RespectCanCollide==true and delta.Magnitude>0,"Guardian sweep contract")
        local center=frame.Position
        local closest,normal,distance=nil,nil,math.huge
        for _,part in workspace:GetDescendants() do
            if not queryEligible(part,params) then continue end
            local half=(part.Size+size)*.5
            local rel=center-part.Position
            if math.abs(rel.X)<half.X and math.abs(rel.Y)<half.Y and math.abs(rel.Z)<half.Z then continue end
            local first,last=0,1
            local hitNormal,crosses=nil,true
            for _,axis in axes do
                local offset,extent,velocity=rel[axis],half[axis],delta[axis]
                if math.abs(velocity)<1e-10 then
                    if math.abs(offset)>=extent then crosses=false;break end
                else
                    local a,b=(-extent-offset)/velocity,(extent-offset)/velocity
                    local near,far=math.min(a,b),math.max(a,b)
                    if near>=first then
                        first=near
                        hitNormal=normals[axis]*(if velocity>0 then -1 else 1)
                    end
                    last=math.min(last,far)
                    if first>last then crosses=false;break end
                end
            end
            if crosses and hitNormal and first<distance then
                closest,normal,distance=part,hitNormal,first
            end
        end
        if closest then
            return {Instance=closest,Normal=normal,Position=center+delta*distance,Distance=delta.Magnitude*distance}
        end
        return nil
    end
end
