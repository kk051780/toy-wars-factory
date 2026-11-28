local function contact(f, owned, signal, count)
 f:check(owned.DestroyAttempts==count, "owned Destroy calls="..tostring(owned.DestroyAttempts))
 f:check(not signal.Connected and f:observerCount()==0, "observer/Destroying connection remains")
 f:assertNoErrors()
end

case("independent_parent_destruction", "FAIL", function()
 local f=fixture()
 local owned=open(f)
 local signal=owned.Destroying.connections[1]
 f.playerGui:Destroy()
 f:assertNoErrors()
 f:check(owned.Destroyed and owned.Parent==nil, "owned descendant remains")
 contact(f,owned,signal,1)
end)

case("independent_unparented_live_gui_still_needs_destroy", "PASS", function()
 local f=fixture()
 local owned=open(f)
 local signal=owned.Destroying.connections[1]
 owned.Parent=nil
 f:check(not owned.Destroyed, "detaching alone destroyed GUI")
 f:heartbeat()
 f:check(owned.Destroyed, "detached live GUI leaked")
 contact(f,owned,signal,1)
end)

case("independent_retirement_disconnects_before_foreign_destroy_listener_fires", "PASS", function()
 local f=fixture()
 local old=open(f)
 local original=old.Destroying.connections[1]
 local observed
 old.Destroying:Connect(function()
  observed={requestConnected=original.Connected, heartbeats=f:observerCount()}
 end)
 f:kill()
 f:heartbeat()
 f:check(observed~=nil and not observed.requestConnected and observed.heartbeats==0,
  "own invalidation destroyed before releasing both subscriptions")
 contact(f,old,original,1)
end)

local function queuedClose()
 local f=fixture()
 local owned=open(f)
 local connection=owned.Destroying.connections[1]
 f.queueThis=owned
 f:close()
 f:check(owned.Destroyed and owned.Parent==nil and f.delivery~=nil, "missing delayed notification")
 return f,owned,connection
end

case("independent_deferred_notice_before_next_heartbeat", "FAIL", function()
 local f,owned,connection=queuedClose()
 f.delivery()
 f:heartbeat()
 contact(f,owned,connection,1)
end)

case("independent_heartbeat_before_deferred_notice_single_destroy", "FAIL", function()
 local f,owned,connection=queuedClose()
 f:heartbeat()
 local restore=open(f)
 f.delivery()
 f:check(f:gui()==restore and f:observerCount()==1 and not connection.Connected,
  "stale work disturbed the next healthy window")
 f:assertNoErrors()
 f:check(owned.DestroyAttempts==1,"completed GUI Destroy calls="..tostring(owned.DestroyAttempts))
end)

case("independent_reopen_before_deferred_notice_single_destroy", "FAIL", function()
 local f,owned,connection=queuedClose()
 local restore=open(f)
 f.delivery()
 f:check(f:gui()==restore and f:observerCount()==1 and not connection.Connected and owned.Destroyed,
  "replacement did not survive a late callback")
 f:assertNoErrors()
 f:check(owned.DestroyAttempts==1,"completed GUI Destroy calls="..tostring(owned.DestroyAttempts))
end)
