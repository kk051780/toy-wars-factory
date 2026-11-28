-- Isolated follow-ups to #1029 comments 7113287926 and 7114096066.
case('playergui_replacement_retires_owned_gui','FAIL',function()
 local f=fixture()
 local old=open(f)
 local previous=f.playerGui
 previous.Parent=nil
 local replacement=f.Instance.new('PlayerGui');replacement.Name='PlayerGui';replacement.Parent=f.player
 local foreign=f.Instance.new('ScreenGui');foreign.Name='ForeignGui';foreign.Parent=replacement
 f:heartbeat()
 f:assertNoErrors()
 f:check(not foreign.Destroyed,'foreign GUI destroyed')
 f:check(old.Destroyed,'old PlayerGui retained shop')
 f:check(f:observerCount()==0,'old PlayerGui retained observer')
 f.playerGui=replacement
 open(f)
 f:check(f:observerCount()==1,'replacement did not reopen cleanly')
end)
case('view_mount_partial_failure_cleans_orphan','FAIL',function()
 local f=fixture()
 open(f);f:close()
 local originalMount=f.cache.view.mount
 f.cache.view.mount=function(...)
  originalMount(...)
  error('fixture fault after ScreenGui is parented before return')
 end
 f:trigger()
 f:assertNoErrors()
 f:check(f:observerCount()==0,'failed request retained observer')
 f:active('TEAM');f:heartbeat()
 f:check(f:gui()==nil,'orphaned shop obscures ACTIVE combat')
end)
