local spectatorSpawnPlaced = setmetatable({}, {__mode="k"})
local function placeSpectatorSpawn(player: Player, character: Model, root: BasePart, hum: Humanoid)
    if spectatorSpawnPlaced[character] or match.phase=="LOBBY" or not player.Neutral
        or hum.Health<=0 or player.Parent~=Players or player.Character~=character then return end
    spectatorSpawnPlaced[character]=true
    root.CFrame=LobbyIsland.spawn("RED")
    task.defer(function()
        -- CharacterAdded runs before the engine's final move to its spawn location.
        -- Correct one observed displacement of this avatar, never an admitted player.
        for _,delay in ipairs({0.25,0.75,2,4,8}) do
            task.wait(delay)
            if player.Parent~=Players or player.Character~=character or not player.Neutral
                or player:GetAttribute("P0D_LateJoinSpectator")~=true or getTeamName(player)~="NONE"
                or match.phase=="LOBBY" or root.Parent~=character or hum.Parent~=character
                or hum.Health<=0 then return end
            if character:IsDescendantOf(workspace) and not LobbyIsland.inLobby(root.Position) then
                root.AssemblyLinearVelocity=Vector3.zero
                root.AssemblyAngularVelocity=Vector3.zero
                root.CFrame=LobbyIsland.spawn("RED")
                return
            end
        end
    end)
end
