-- Native Luau fixture. The installed script is the exact selected LocalScript.
-- Fixture vectors, rays, and replicated properties are deterministic doubles.

-- Plain Native Luau fixtures. The prompt selector models the Studio-observed case.
local deferred = false
local deliverDisconnected = false
local pending = {}
local function flush()
	while #pending > 0 do
		table.remove(pending, 1)()
	end
end

local function signal()
	local listeners = {}
	local s = {}
	function s:Connect(callback)
		local item = { active = true, callback = callback }
		table.insert(listeners, item)
		return {
			Disconnect = function()
				item.active = false
			end,
		}
	end
	function s:Fire(...)
		for _, item in ipairs(table.clone(listeners)) do
			if item.active then
				if deferred then
					local args = table.pack(...)
					table.insert(pending, function()
						if item.active or deliverDisconnected then
							item.callback(table.unpack(args, 1, args.n))
						end
					end)
				else
					item.callback(...)
				end
			end
		end
	end
	function s:count()
		local count = 0
		for _, item in ipairs(listeners) do
			if item.active then count += 1 end
		end
		return count
	end
	return s
end

local function node(class, name, enabled)
	local changes = signal()
	local attributes = {}
	local attributeSignals = {}
	local attrs = {
		Name = name, Enabled = enabled, Children = {},
		DescendantAdded = signal(), DescendantRemoving = signal(),
	}
	local function descendants(_, out)
		out = out or {}
		for _, child in ipairs(attrs.Children) do
			table.insert(out, child)
			child:GetDescendants(out)
		end
		return out
	end
	return setmetatable({}, {
		__index = function(_, key)
			if key == "IsA" then
				return function(_, requested)
					return requested == class or requested == "BasePart" and class == "Part"
				end
			elseif key == "GetPropertyChangedSignal" then
				return function(_, property)
					assert(property == "Enabled")
					return changes
				end
			elseif key == "FindFirstChild" or key == "FindFirstChildOfClass" then
				return function(_, name)
					for _, child in ipairs(attrs.Children) do
						if key == "FindFirstChild" and child.Name == name
							or key == "FindFirstChildOfClass" and child:IsA(name) then return child end
					end
					return nil
				end
			elseif key == "IsDescendantOf" then
				return function(obj, ancestor)
					local cursor = obj.Parent
					while cursor do
						if cursor == ancestor then return true end
						cursor = cursor.Parent
					end
					return false
				end
			elseif key == "GetAttributeChangedSignal" then
				return function(_, name)
					if not attributeSignals[name] then attributeSignals[name] = signal() end
					return attributeSignals[name]
				end
			elseif key == "SetAttribute" then
				return function(_, name, value)
					if attributes[name] == value then return end
					attributes[name] = value
					if attributeSignals[name] then attributeSignals[name]:Fire() end
				end
			elseif key == "GetAttribute" then
				return function(_, name) return attributes[name] end
			elseif key == "GetDescendants" then
				return descendants
			end
			return attrs[key]
		end,
		__newindex = function(_, key, nextValue)
			if attrs[key] == nextValue then return end
			attrs[key] = nextValue
			if key == "Enabled" then changes:Fire() end
		end,
	})
end

local function parent(child, model)
	local oldParent = child.Parent
	if oldParent then
		local cursor = oldParent
		while cursor do
			cursor.DescendantRemoving:Fire(child)
			for _, desc in ipairs(child:GetDescendants()) do cursor.DescendantRemoving:Fire(desc) end
			cursor = cursor.Parent
		end
		table.remove(oldParent.Children, assert(table.find(oldParent.Children, child)))
	end
	child.Parent = model
	if model then
		table.insert(model.Children, child)
		local cursor = model
		while cursor do
			cursor.DescendantAdded:Fire(child)
			for _, desc in ipairs(child:GetDescendants()) do cursor.DescendantAdded:Fire(desc) end
			cursor = cursor.Parent
		end
	end
end



local RELAY = "EGGRUMBLE_ClassicEggRelay"
local ROUND = "EGGRUMBLE_RelayPresentationRoundV1"
local TEAM = "EGGRUMBLE_RelayPresentationTeam"
local READY = "EGGRUMBLE_RelayPresentationReady"
local HEIGHT = "EGGRUMBLE_RelayPresentationHeight"
local MODE = "EGGRUMBLE_QueuedMode"
local ELIMINATED = "EGGRUMBLE_Eliminated"
local PHASE = "EGGRUMBLE_MatchPhase"

local vectorMetatable = {}
local function v(x, y, z)
	return setmetatable({ X = x, Y = y, Z = z, Magnitude = math.sqrt(x*x + y*y + z*z) }, vectorMetatable)
end
vectorMetatable.__add = function(a, b) return v(a.X + b.X, a.Y + b.Y, a.Z + b.Z) end
vectorMetatable.__sub = function(a, b) return v(a.X - b.X, a.Y - b.Y, a.Z - b.Z) end

local function add(class, name, ancestor)
	local child = node(class, name)
	parent(child, ancestor)
	return child
end

local function avatar(world, position)
	local character = add("Model", "Character", world)
	local humanoid = add("Humanoid", "Humanoid", character)
	humanoid.Health = 100
	local root = add("Part", "HumanoidRootPart", character)
	root.Position = position
	return character, root, humanoid
end

local function seat(world, position, team, carrying, round, legacy)
	local character, root, humanoid = avatar(world, position)
	local player = node("Player", "Player")
	player.Character = character
	player.CharacterAdded = signal()
	player.CharacterRemoving = signal()
	player:SetAttribute(MODE, "TEAM")
	local prompt = add("ProximityPrompt", RELAY, root)
	prompt.Enabled = carrying
	prompt.RequiresLineOfSight = true
	prompt.MaxActivationDistance = 8
	if not legacy then
		prompt:SetAttribute(ROUND, round or 1)
		prompt:SetAttribute(TEAM, team)
		prompt:SetAttribute(READY, carrying)
		prompt:SetAttribute(HEIGHT, 4)
	end
	return { variant = player, character = character, root = root, humanoid = humanoid, prompt = prompt }
end

local function install(f, studio)
	local services = {
		Players = { LocalPlayer = f.a.variant, GetPlayers = function() return f.roster end },
		RunService = { IsStudio = function() return studio end, Heartbeat = f.heartbeat },
	}
	for _, actor in ipairs(f.roster) do actor.Parent = services.Players end
	local game = { GetService = function(_, name) return assert(services[name]) end }
	local workspace = f.world
	local Vector3 = { new = v }
	local RaycastParams = { new = function() return {} end }
	local Enum = { RaycastFilterType = { Exclude = "Exclude" } }
local task={spawn=function(worker) worker() end}
-- @RELAY_PRESENTATION_MOUNTED@

end

local function fixture(legacy)
	local f = { heartbeat = signal(), rays = {} }
	f.world = node("Workspace", "Workspace")
	local world = f.world
	local lobby = add("Folder", "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW", world)
	f.arena = add("Folder", "TEAM_Arena", lobby)
	f.arena:SetAttribute(PHASE, "ACTIVE")
	f.a = seat(world, v(0, 3, 0), "RED", true, 1, legacy)
	f.b = seat(world, v(5, 3, 0), "RED", true, 1, legacy)
	f.c = seat(world, v(2, 3, 0), "BLUE", true, 1, legacy)
	f.roster = { f.a.variant, f.b.variant, f.c.variant }
	function f.update()
		f.heartbeat:Fire(0.125)
	end
	function world:Raycast(origin, delta, params)
		table.insert(f.rays, { origin = origin, delta = delta,
			filter = table.clone(params.FilterDescendantsInstances),
			collidable = params.RespectCanCollide, filterType = params.FilterType })
		if f.wall then return { Instance = f.wall } end
		return nil
	end
	return f
end

local function visible(prompt)
	assert(prompt.Enabled == true and prompt.RequiresLineOfSight == false and prompt.MaxActivationDistance == 8, "peer not locally projected")
end

local function hidden(prompt)
	assert(prompt.MaxActivationDistance == 0 and prompt.RequiresLineOfSight == true, "ineligible peer must have zero local activation range")
end

local count = 0
local function check(name, test)
	local passed, reason = pcall(test)
	assert(passed, name .. ": " .. tostring(reason))
	count += 1
	print("PASS", name)
end

check("same_team_at_five_studs_excludes_both_avatars_and_keeps_original_radius", function()
	local f = fixture(false)
	install(f, true)
	visible(f.b.prompt)
	assert(f.b.prompt.Parent == f.b.root and f.b.prompt.MaxActivationDistance == 8)
	assert(not f.a.prompt.Enabled and f.a.prompt.RequiresLineOfSight)
	assert(#f.rays == 1)
	local ray = f.rays[1]
	assert(ray.origin.X == 0 and ray.origin.Y == 4 and ray.origin.Z == 0)
	assert(ray.delta.X == 5 and ray.delta.Y == 0 and ray.delta.Z == 0)
	assert(#ray.filter == 2 and ray.filter[1] == f.a.character and ray.filter[2] == f.b.character)
	assert(ray.collidable == true and ray.filterType == "Exclude")
end)

check("metadata_valid_closer_enemy_stays_disabled_even_after_enabled_replication", function()
	local f = fixture(false)
	install(f, true)
	hidden(f.c.prompt)
	f.c.prompt.Enabled = true -- engine property update independent of metadata
	f.update()
	hidden(f.c.prompt)
	assert(f.c.prompt:GetAttribute(READY) == true)
end)

check("a_low_collidable_wall_disables_the_prompt_and_wall_clear_recovers", function()
	local f = fixture(false)
	f.wall = { CanCollide = true }
	install(f, true)
	hidden(f.b.prompt)
	assert(#f.rays == 1 and f.rays[1].origin.Y == 4)
	f.wall = nil
	f.update()
	visible(f.b.prompt)
	assert(f.b.prompt:GetAttribute(READY) == true)
	f.wall = { CanCollide = true }
	f.update()
	hidden(f.b.prompt)
end)

check("noncollidable_decoration_does_not_block_the_server_matching_ray", function()
	local f = fixture(false)
	f.wall = { CanCollide = false }
	install(f, true)
	visible(f.b.prompt)
end)

check("exact_radius_and_reentry_do_not_require_server_toggle", function()
	local f = fixture(false)
	f.b.root.Position = v(8, 3, 0)
	install(f, true)
	visible(f.b.prompt)
	f.b.root.Position = v(8.01, 3, 0)
	f.update()
	hidden(f.b.prompt)
	assert(#f.rays == 1)
	f.b.root.Position = v(7.75, 6, 0) -- inside horizontal reach, outside the original 3D sphere
	f.update()
	hidden(f.b.prompt)
	assert(#f.rays == 1)
	f.b.root.Position = v(7, 3, 0)
	f.update()
	visible(f.b.prompt)
	assert(f.b.prompt:GetAttribute(READY) == true)
end)

check("root_height_exact_boundary_and_vertical_excess", function()
	local f = fixture(false)
	f.b.root.Position = v(3, 7, 0)
	install(f, true)
	visible(f.b.prompt)
	assert(f.rays[1].delta.Y == 4)
	f.b.root.Position = v(3, 7.01, 0)
	f.update()
	hidden(f.b.prompt)
	assert(#f.rays == 1)
end)

check("ready_attribute_follows_server_while_self_filter_uses_replication", function()
	local f = fixture(false)
	install(f, true)
	f.b.prompt:SetAttribute(READY, false)
	f.update()
	hidden(f.b.prompt)
	f.a.prompt.Enabled = true
	assert(not f.a.prompt.Enabled)
	f.b.prompt:SetAttribute(READY, true)
	f.update()
	visible(f.b.prompt)
end)

check("different_rounds_and_incomplete_contract_never_project", function()
	local f = fixture(false)
	f.b.prompt:SetAttribute(ROUND, 2)
	install(f, true)
	hidden(f.b.prompt)
	f.a.prompt:SetAttribute(ROUND, 2)
	f.update()
	visible(f.b.prompt)
	f.b.prompt:SetAttribute(HEIGHT, nil)
	f.update()
	hidden(f.b.prompt)
	f.b.prompt:SetAttribute(HEIGHT, 4)
	f.b.prompt:SetAttribute(TEAM, nil)
	f.update()
	hidden(f.b.prompt)
end)

check("finished_round_and_abandoned_team_clear_preserved_prompts", function()
	local f = fixture(false)
	install(f, true)
	visible(f.b.prompt)
	f.arena:SetAttribute(PHASE, "FINISHED")
	f.update()
	hidden(f.b.prompt)
	f.arena:SetAttribute(PHASE, "ACTIVE")
	f.a.variant:SetAttribute(MODE, nil)
	f.update()
	hidden(f.b.prompt)
end)

check("replacement_body_cannot_reuse_stale_own_metadata", function()
	local f = fixture(false)
	install(f, true)
	visible(f.b.prompt)
	f.a.variant.CharacterRemoving:Fire(f.a.character)
	local next = seat(f.world, v(0, 3, 0), "RED", true, 1, true)
	f.a.variant.Character = next.character
	f.a.variant.CharacterAdded:Fire(next.character)
	f.update()
	hidden(f.b.prompt)
	assert(not next.prompt.Enabled)
	for name, value in pairs({ [ROUND] = 1, [TEAM] = "RED", [HEIGHT] = 4, [READY] = true }) do
		next.prompt:SetAttribute(name, value)
	end
	f.update()
	visible(f.b.prompt)
end)

check("leave_or_peer_respawn_revokes_the_previous_instance", function()
	local f = fixture(false)
	install(f, true)
	visible(f.b.prompt)
	table.remove(f.roster, 2)
	f.update()
	hidden(f.b.prompt)
	table.insert(f.roster, 2, f.b.variant)
	f.update()
	visible(f.b.prompt)
	local old = f.b.prompt
	local next = seat(f.world, v(4, 3, 0), "RED", true, 1, false)
	f.b.variant.Character = next.character
	f.update()
	hidden(old)
	visible(next.prompt)
end)

check("eliminated_and_dead_viewer_or_carrier_do_not_project", function()
	local f = fixture(false)
	install(f, true)
	f.a.variant:SetAttribute(ELIMINATED, true)
	f.update()
	hidden(f.b.prompt)
	f.a.variant:SetAttribute(ELIMINATED, nil)
	f.b.humanoid.Health = 0
	f.update()
	hidden(f.b.prompt)
	f.b.humanoid.Health = 50
	f.update()
	visible(f.b.prompt)
	f.a.humanoid.Health = 0
	f.update()
	hidden(f.b.prompt)
end)

check("old_host_peer_prompts_keep_their_original_engine_presentation", function()
	local f = fixture(true)
	install(f, true)
	assert(f.b.prompt.Enabled and f.b.prompt.RequiresLineOfSight)
	assert(f.c.prompt.Enabled and f.c.prompt.RequiresLineOfSight)
	assert(not f.a.prompt.Enabled and #f.rays == 0)
end)

check("other_prompts_and_non_studio_are_untouched", function()
	local f = fixture(false)
	local deposit = add("ProximityPrompt", "OwnEggDeposit", f.a.root)
	deposit.Enabled = true
	local nested = add("Folder", "Decoration", f.b.root)
	local fake = add("ProximityPrompt", RELAY, nested)
	fake.Enabled = true
	fake:SetAttribute(ROUND, 2)
	install(f, false)
	assert(f.heartbeat:count() == 0 and f.a.prompt.Enabled and f.b.prompt.Enabled and f.b.prompt.RequiresLineOfSight)
	install(f, true)
	assert(deposit.Enabled and fake.Enabled)
end)

check("peer_refresh_is_bounded_instead_of_raycasting_every_frame", function()
	local f = fixture(false)
	install(f, true)
	assert(#f.rays == 1)
	for _ = 1, 7 do f.heartbeat:Fire(1/60) end
	assert(#f.rays == 1)
	f.heartbeat:Fire(1/60)
	assert(#f.rays == 2)
end)


check("known_enemy_server_enabled_before_heartbeat_cannot_restore_its_positive_range", function()
	local f = fixture(false)
	f.c.prompt.Enabled = false
	f.c.prompt:SetAttribute(READY, false)
	install(f, true)
	hidden(f.c.prompt)
	deferred = true
	f.c.prompt.Enabled = true
	assert(f.c.prompt.Enabled and f.c.prompt.MaxActivationDistance == 0)
	f.c.prompt:SetAttribute(READY, true)
	assert(f.c.prompt.Enabled and f.c.prompt.MaxActivationDistance == 0)
	flush()
	hidden(f.c.prompt)
	deferred = false
end)

check("eligible_ally_server_disabled_with_stale_ready_cannot_be_reenabled", function()
	local f = fixture(false)
	install(f, true)
	visible(f.b.prompt)
	deferred = true
	f.b.prompt.Enabled = false
	assert(f.b.prompt:GetAttribute(READY) == true)
	f.update()
	flush()
	assert(not f.b.prompt.Enabled)
	hidden(f.b.prompt)
	f.b.prompt:SetAttribute(READY, false)
	f.b.prompt.Enabled = true
	flush()
	hidden(f.b.prompt)
	f.b.prompt:SetAttribute(READY, true)
	flush()
	visible(f.b.prompt)
	deferred = false
end)

check("wall_range_and_reentry_repeat_without_server_availability_toggle", function()
	local f = fixture(false)
	install(f, true)
	for _ = 1, 4 do
		f.wall = { CanCollide = true }
		f.update()
		hidden(f.b.prompt)
		f.wall = nil
		f.b.root.Position = v(8.01, 3, 0)
		f.update()
		hidden(f.b.prompt)
		f.b.root.Position = v(5, 3, 0)
		f.update()
		visible(f.b.prompt)
		assert(f.b.prompt.Enabled and f.b.prompt:GetAttribute(READY) == true)
	end
end)

check("original_range_is_bound_to_the_exact_prompt_and_retained_through_rebind", function()
	local f = fixture(false)
	f.b.prompt.MaxActivationDistance = 6
	f.b.root.Position = v(6.01, 3, 0)
	install(f, true)
	hidden(f.b.prompt)
	table.remove(f.roster, 2)
	f.update()
	assert(f.b.prompt:GetPropertyChangedSignal("Enabled"):count() == 0)
	assert(f.b.prompt:GetAttributeChangedSignal(READY):count() == 0)
	parent(f.b.prompt, nil)
	f.update()
	assert(f.b.prompt.MaxActivationDistance == 6)
	parent(f.b.prompt, f.b.root)
	table.insert(f.roster, 2, f.b.variant)
	f.b.root.Position = v(6, 3, 0)
	f.update()
	assert(f.b.prompt.Enabled and f.b.prompt.MaxActivationDistance == 6 and not f.b.prompt.RequiresLineOfSight)
end)

check("deferred_signal_from_released_binding_cannot_act_on_rebound_same_prompt", function()
	local f = fixture(false)
	install(f, true)
	visible(f.b.prompt)
	local raysBefore = #f.rays
	deferred = true
	deliverDisconnected = true
	table.remove(f.roster, 2)
	f.update() -- queue the release
	table.insert(pending, function()
		assert(f.b.prompt:GetPropertyChangedSignal("Enabled"):count() == 0)
		assert(f.b.prompt:GetAttributeChangedSignal(READY):count() == 0)
		table.insert(f.roster, 2, f.b.variant)
	end)
	f.update() -- queue rebind before the original watcher runs
	f.b.prompt.Enabled = false
	f.b.prompt.Enabled = true
	f.b.prompt:SetAttribute(READY, false)
	f.b.prompt:SetAttribute(READY, true)
	flush()
	visible(f.b.prompt)
	assert(#f.rays == raysBefore + 1, "an escaped callback from the retired binding executed")
	assert(f.b.prompt:GetPropertyChangedSignal("Enabled"):count() == 1)
	assert(f.b.prompt:GetAttributeChangedSignal(READY):count() == 1)
	deliverDisconnected = false
	deferred = false
end)

check("initial_viewer_or_carrier_missing_humanoid_is_suppressed_and_recovers", function()
	local f = fixture(false)
	parent(f.a.humanoid, nil)
	parent(f.b.humanoid, nil)
	install(f, true)
	hidden(f.b.prompt)
	assert(#f.rays == 0 and f.b.prompt.Enabled)
	parent(f.a.humanoid, f.a.character)
	f.update()
	hidden(f.b.prompt)
	assert(#f.rays == 0)
	parent(f.b.humanoid, f.b.character)
	f.update()
	visible(f.b.prompt)
	assert(#f.rays == 1)
end)

check("zero_overlap_applies_zero_range_and_keeps_peer_availability_untouched", function()
	local f = fixture(false)
	f.c.root.Position = f.a.root.Position
	install(f, true)
	assert((f.c.root.Position - f.a.root.Position).Magnitude == 0)
	hidden(f.c.prompt)
	assert(f.c.prompt.Enabled)
	-- The fixture checks source properties only. The engine may compare the
	-- exact zero boundary differently. It needs a separate Studio witness.
	print("STUDIO_REQUIRED", "exact_zero_overlap_with_MaxActivationDistance_0")
end)

print("PROJECTION_NATIVE_PASS", count)
