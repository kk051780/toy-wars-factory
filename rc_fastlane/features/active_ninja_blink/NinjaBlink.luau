--!strict
-- The exact published owner row supplies the combat timing and all five stage values.
local source={
["NINJA-031"]={["id"]="NINJA-031",["name"]="瞬歩",["rarity"]="C",["description"]="短距離前方移動",["roles"]={"NINJA"},["catalogSource"]="7203813893",["cd"]=16,["energy"]=30,["metrics"]={{["label"]="前方移動stud",["values"]={5,7,9,11,13},["note"]=""},{["label"]="発動予告秒",["values"]={0.18,0.18,0.18,0.18,0.18},["note"]=""}},["forms"]={"踵の薄板と短影","足跡が連続","足甲に折線板が開き斜め指定","黒羽形の踵装具","月影の薄い残像と踏み止め姿勢"},["designSource"]="7204247109",["specification"]="- NINJA-031 **瞬歩** [C]｜前方移動stud: 5/7/9/11/13｜発動予告秒: 0.18/0.18/0.18/0.18/0.18｜CD16s/E30\n- 造形/リグ：炭色の足甲、鈍い銀の踵板、赤褐色組紐\n- モーション：腰を落とし0.18秒の方向予告→安全経路の短移動→着地踏み止め\n- 音響：布擦れ、短い足音、着地の乾いた音\n- S0 踵の薄板と短影 → S1 足跡が連続 → S2 足甲に折線板が開き斜め指定 → S3 黒羽形の踵装具 → S4 月影の薄い残像と踏み止め姿勢\n- 対抗/回帰：壁で停止し位置を偽らない、無敵追加なし"},
}
local Blink={}
Blink.config=table.freeze(source["NINJA-031"])

function Blink.isGrounded(hum: Humanoid): boolean
    return hum.SeatPart==nil and not hum.Sit and not hum.PlatformStand
        and hum.FloorMaterial~=Enum.Material.Air and hum.FloorMaterial~=Enum.Material.Water
end

function Blink.direction(forward: Vector3,velocity: Vector3,walkSpeed: number,stage: number): Vector3?
    local flat=Vector3.new(forward.X,0,forward.Z)
    flat=if flat.Magnitude>.01 then flat.Unit else Vector3.new(1,0,0)
    local movement=Vector3.new(velocity.X,0,velocity.Z)
    local speed=movement.Magnitude
    if speed<2 then return flat end
    if speed>math.clamp(walkSpeed,0,64)*1.5 then return nil end
    if stage<2 then
        local cross=movement-flat*movement:Dot(flat)
        local tell=Blink.config.metrics[2].values[stage+1]
        return if cross.Magnitude*tell<=.6 then flat else nil
    end
    -- Keep a promised forward diagonal aligned with the movement already held.
    local track=movement.Unit
    return if track:Dot(flat)>=.5 then track else nil
end

function Blink.inside(arena: BasePart,position: Vector3): boolean
    return math.abs(position.X-arena.Position.X)<=arena.Size.X*.5-4.5
        and math.abs(position.Z-arena.Position.Z)<=arena.Size.Z*.5-4.5
end

function Blink.landing(arena: BasePart,character: Model,origin: Vector3,facing: Vector3,amount: number): Vector3?
    if not arena.Parent or not arena.Anchored or not arena.CanCollide or not Blink.inside(arena,origin) then
        return nil
    end
    local ray=RaycastParams.new()
    ray.FilterType=Enum.RaycastFilterType.Exclude
    ray.FilterDescendantsInstances={character}
    ray.RespectCanCollide=true
    -- Retain the existing SevenRoleCombat safeMove nine-ray cross-section.
    -- It catches torso, low and overhead obstructions and narrow gate jambs.
    local right=Vector3.new(-facing.Z,0,facing.X)
    local distance=amount
    for _,height in ipairs({-1.1,2,4.6}) do
        for _,side in ipairs({-1.3,0,1.3}) do
            local eye=origin+Vector3.new(0,height,0)+right*side
            local hit=workspace:Raycast(eye,facing*amount,ray)
            if hit then distance=math.min(distance,math.max(0,hit.Distance-3)) end
        end
    end
    if distance<3 then return nil end
    -- Reuse the guardian's continuous body sweep between the sampled rays.
    local body=Vector3.new(3.2,4.5,3.2)
    local sweep=workspace:Blockcast(CFrame.new(origin),body,facing*distance,ray)
    if sweep then distance=math.min(distance,math.max(0,sweep.Distance-.35)) end
    if distance<3 then return nil end
    local projected=origin+facing*distance
    if not Blink.inside(arena,projected) then return nil end
    local ground=workspace:Raycast(projected+Vector3.new(0,6,0),Vector3.new(0,-17,0),ray)
    if not ground or not ground.Instance:IsA("BasePart") or not ground.Instance.Anchored
        or not ground.Instance.CanCollide or ground.Normal.Y<.65 then return nil end
    local target=ground.Position+Vector3.new(0,3,0)
    if math.abs(target.Y-origin.Y)>3.5 then return nil end
    local overlap=OverlapParams.new()
    overlap.FilterType=Enum.RaycastFilterType.Exclude
    overlap.FilterDescendantsInstances={character}
    overlap.RespectCanCollide=true
    if #workspace:GetPartBoundsInBox(CFrame.new(target),body,overlap)>0 then return nil end
    return target
end

return table.freeze(Blink)
