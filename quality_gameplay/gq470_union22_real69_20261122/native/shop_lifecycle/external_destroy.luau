-- A closed shop can be destroyed by a different owner or with its parent.
-- The older f:close() sequence invokes the paired View's own onClose callback.
local function externallyDestroyed()
 local f=fixture()
 local old=open(f)
 local connection=old.Destroying.connections[1]
 f.queueThis=old
 old:Destroy()
 f:check(old.Destroyed and old.Parent==nil and #old:GetChildren()==0 and f.delivery~=nil,
  "external Destroy completed while its notification was deferred")
 f:check(connection.Connected and f:observerCount()==1,"old request has yet to observe the external Destroy")
 return f,old,connection
end

case("external_destroy_heartbeat_before_notification","FAIL",function()
 local f,old,connection=externallyDestroyed()
 f:heartbeat()
 local nextWindow=open(f)
 f.delivery()
 f:assertNoErrors()
 f:check(not connection.Connected and f:observerCount()==1 and f:gui()==nextWindow,
  "late old notification cannot retire a new request")
 f:check(old.DestroyAttempts==1,"externally destroyed window received "..tostring(old.DestroyAttempts).." Destroy calls")
end)

case("external_destroy_reopen_before_notification","FAIL",function()
 local f,old,connection=externallyDestroyed()
 local nextWindow=open(f)
 f.delivery()
 f:heartbeat()
 f:check(not connection.Connected and f:observerCount()==1 and f:gui()==nextWindow,
  "old release during reopen cannot retire the new window")
 f:check(old.DestroyAttempts==1,"externally destroyed window received "..tostring(old.DestroyAttempts).." Destroy calls")
end)

case("external_destroy_parent_before_notification","FAIL",function()
 local f=fixture()
 local old=open(f)
 local connection=old.Destroying.connections[1]
 f.queueThis=old
 f.playerGui:Destroy()
 f:check(old.Destroyed and #old:GetChildren()==0 and f.delivery~=nil,"actual parent Destroy queued descendant notice")
 local replacement=f.Instance.new("PlayerGui");replacement.Name="PlayerGui";replacement.Parent=f.player
 f.playerGui=replacement
 f:heartbeat()
 local nextWindow=open(f)
 f.delivery()
 f:check(not connection.Connected and nextWindow.Parent==replacement and f:observerCount()==1,
  "replacement PlayerGui gets only its own new request")
 f:check(old.DestroyAttempts==1,"parent-destroyed window received "..tostring(old.DestroyAttempts).." Destroy calls")
end)

case("owned_detach_retires_nonempty_window","PASS",function()
 local f=fixture()
 local old=open(f)
 old.Parent=nil
 f:check(not old.Destroyed and #old:GetChildren()>0,"real detachable window remains live before retirement")
 f:heartbeat()
 f:check(old.Destroyed and old.DestroyAttempts==1 and f:observerCount()==0,"detached owned view was retired")
end)

for _,failAt in ipairs({"before_build","after_mount"}) do
 case("owned_mount_fault_"..failAt,"PASS",function()
  local f=fixture()
  open(f);f:close()
  local original=assert(f.cache.view.mountOwned)
  local captured
  f.cache.view.mountOwned=function(parent,snapshot,window)
   captured=window.gui
   if failAt=="after_mount" then original(parent,snapshot,window) end
   error("controlled existing mountOwned failure")
  end
  f:trigger()
  f:assertNoErrors()
  f:check(captured and captured.Destroyed and captured.DestroyAttempts==1
   and not f:gui() and f:observerCount()==0,"failed own mount must destroy its window")
  f.cache.view.mountOwned=original
  open(f)
 end)
end
