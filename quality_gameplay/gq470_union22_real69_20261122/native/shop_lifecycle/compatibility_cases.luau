local expectedMount = @EXPECTED_MOUNT@

case("declared_mount_capability_matches_the_pair", "PASS", function()
 local f = fixture()
 local before = #f.created
 if expectedMount then
  local first = open(f)
  f:close()
  f:check(first.Destroyed and f:gui() == nil, "normal close left a shop")
  local second = open(f)
  f:check(second ~= first, "retry reused a closed window")
  f:close()
  f:check(second.Destroyed and f:gui() == nil, "second close left a shop")
  f:check(#f.warnings == 0 and f:observerCount() == 0, "compatible reopen left warnings or observers")
 else
  for _ = 1, 3 do
   f:trigger()
   noWindow(f, "incompatible ShopView mounted an orphan")
   f:check(#f.created == before and f:observerCount() == 0, "incompatible mount allocated UI or retained an observer")
  end
  f:check(#f.warnings == 3, "the refusal did not retire each attempted request")
  for _, warning in ipairs(f.warnings) do
   f:check(tostring(warning[2]):find("ShopView does not support an owned preview mount", 1, true) ~= nil,
    "wrong incompatibility diagnostic")
  end
 end
end)

case("renderer_legacy_mount_remains_callable", "PASS", function()
 local f = fixture()
 f:trigger()
 f:close()
 local view = f.cache.view
 local catalog = f.cache.catalog
 local container = f.Instance.new("PlayerGui")
 local snapshot = {catalog = catalog.list(), robuxEnabled = false}
 local original = view.mount(container, snapshot, nil)
 f:check(original.Parent == container, "legacy mount did not publish its window")
 local replacement = view.mount(container, snapshot, nil)
 f:check(original.Destroyed and replacement ~= original and replacement.Parent == container,
  "legacy mounting no longer replaces its old renderer window")
 replacement:FindFirstChild("ShopWindow"):FindFirstChild("Close").Activated:Fire()
 f:check(replacement.Destroyed and container:FindFirstChild("EGGRUMBLE_LobbyShop") == nil,
  "legacy renderer's close button stopped working")
 f:assertNoErrors()
end)

if not expectedMount then
 case("refusal_leaves_a_prior_same_named_window_owned_by_its_caller", "PASS", function()
  local f = fixture()
  local prior = f.Instance.new("ScreenGui")
  prior.Name = "EGGRUMBLE_LobbyShop"
  prior.Parent = f.playerGui
  local before = #f.created
  f:trigger()
  f:heartbeat()
  f:check(f:gui() == prior and not prior.Destroyed, "incompatible renderer destroyed another window")
  f:check(#f.created == before and f:observerCount() == 0, "incompatible mount allocated or retained work")
 end)
end
