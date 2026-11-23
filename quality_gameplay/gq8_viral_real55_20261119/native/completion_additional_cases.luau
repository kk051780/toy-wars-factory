-- Exactly two extra cases. The original normal control and two spontaneous
-- completion cases run before this file and remain byte-identical.

do
    local name="old_normal_completion_while_new_capture"
    local f=newFixture(name,false)
    f:toggleConsent();f:cue(10,1,"EGG_STEAL")
    f:resolvePending("Success","CapturingAlready")
    f:advance(15)
    observe(name,"old_normal_timer_stop",f.activeRequest==nil and #f.stops==1 and f.toggle.Text=="録画待機 ON",f:summary())
    f:advance(18);f:cue(10,2,"EGG_DELIVER")
    f:resolvePending("Success","CapturingAlready")
    observe(name,"new_capture_started_before_old_completion",f:activeSeq()==2 and f.toggle.Text=="● 録画中",f:summary())
    f:advance(18.1);f:complete(1,"Success")
    observe(name,"old_normal_clip_still_saves",f:promptsFrom(1)==1,f:summary())
    observe(name,"old_completion_preserves_new_recording",f:activeSeq()==2 and f.toggle.Text=="● 録画中" and #f.stops==1,f:summary())
    f:advance(27);f:complete(2,"Success")
    observe(name,"new_normal_stop_and_save",f.activeRequest==nil and f.toggle.Text=="録画待機 ON" and f:promptsFrom(2)==1 and #f.stops==2,f:summary())
    f:finish()
end

do
    local name="conditional_completion_before_start_return"
    local f=newFixture(name,false)
    f:toggleConsent();f:cue(10,1,"EGG_STEAL")
    observe(name,"pending_start_control",f:pendingCount()==1 and f.activeRequest==nil and #f.requests==1,f:summary())
    f:advance(.1);f:completeBeforeStartReturn(1,"ScreenSizeChanged")
    observe(name,"pending_completion_ui_idle",f.toggle.Text=="録画待機 ON" and f:pendingCount()==1 and f.activeRequest==nil,f:summary())
    f:advance(3);f:cue(10,2,"EGG_DELIVER")
    observe(name,"unfinished_start_remains_serialized",#f.requests==1 and f:requestsFrom(2)==0 and f:pendingCount()==1,f:summary())
    f:advance(3.1);f:resolvePending("Success","CapturingAlready")
    observe(name,"completed_success_return_does_not_record",f:pendingCount()==0 and f.activeRequest==nil and f.toggle.Text=="録画待機 ON",f:summary())
    f:advance(6);f:cue(10,3,"EGG_DELIVER")
    observe(name,"fresh_cue_after_completed_return",f:requestsFrom(3)==1 and f:pendingCount()==1,f:summary())
    if f:pendingCount()>0 then
        f:resolvePending("Success","CapturingAlready")
        f:advance(15);f:complete(3,"Success")
    end
    f:finish()
end

local extendedPass,extendedRed=0,0
for _,entry in ipairs(observations) do if entry.passed then extendedPass+=1 else extendedRed+=1 end end
print("EXTENDED_TOTAL\t"..#observations.."\tPASS="..extendedPass.."\tRED="..extendedRed)
