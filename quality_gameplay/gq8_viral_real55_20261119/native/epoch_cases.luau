-- Common external schedule and expected contract; identical for baseline/candidate.
-- CapturingAlready is used for an overlapping request, avoiding an assumption
-- that the real API can successfully run two simultaneous captures.

do
    local name="normal_15s_save"
    local f=newFixture(name,false)
    f:cue(10,1,"EGG_STEAL")
    observe(name,"default_off",#f.requests==0 and #f.prompts==0 and f.toggle.Text=="録画 OFF",f:summary())
    f:toggleConsent()
    f:advance(3)
    f:cue(10,2,"EGG_STEAL")
    observe(name,"opt_in_pending",f:pendingCount()==1 and f.activeRequest==nil,f:summary())
    f:resolvePending("Success","CapturingAlready")
    observe(name,"normal_start",f:activeSeq()==2 and f.toggle.Text=="● 録画中",f:summary())
    f:advance(17.999)
    observe(name,"before_15s",f:activeSeq()==2 and #f.stops==0,f:summary())
    f:advance(18)
    observe(name,"after_15s",f.activeRequest==nil and #f.stops==1 and f.toggle.Text=="録画待機 ON",f:summary())
    f:complete(2,"Success")
    observe(name,"normal_completion_save",f:promptsFrom(2)==1,f:summary())
    f:finish()
end

do
    local name="epoch_pending_success"
    local f=newFixture(name,false)
    f:toggleConsent()
    f:cue(10,1,"EGG_STEAL")
    observe(name,"old_start_pending",f:pendingCount()==1 and f.activeRequest==nil,f:summary())
    f:advance(.1)
    f:cue(11,2,"EGG_DELIVER")
    observe(name,"epoch_no_parallel_start",#f.requests==1 and f:pendingCount()==1,f:summary())
    observe(name,"epoch_pending_ui_idle",f.toggle.Text=="録画待機 ON",f:summary())
    f:advance(.2)
    f:resolvePending("Success","CapturingAlready")
    observe(name,"stale_success_stopped",f.activeRequest==nil and #f.stops==1 and f.toggle.Text=="録画待機 ON",f:summary())
    f:complete(1,"Success")
    observe(name,"old_epoch_save_fenced",f:promptsFrom(1)==0,f:summary())
    f:advance(3)
    f:cue(11,3,"EGG_DELIVER")
    observe(name,"fresh_cue_can_start",f:requestsFrom(3)==1 and f:pendingCount()==1,f:summary())
    f:resolvePending("Success","CapturingAlready")
    observe(name,"fresh_cue_records",f:activeSeq()==3,f:summary())
    f:finish()
end

do
    local name="off_on_pending_serialized"
    local f=newFixture(name,false)
    f:toggleConsent()
    f:cue(10,1,"EGG_STEAL")
    f:advance(.1);f:toggleConsent()
    f:advance(.2);f:toggleConsent()
    f:advance(3);f:cue(10,2,"EGG_DELIVER")
    observe(name,"second_start_suppressed",#f.requests==1 and f:requestsFrom(2)==0 and f:pendingCount()==1,f:summary())
    f:advance(3.1)
    f:resolvePending("Success","CapturingAlready")
    observe(name,"old_return_stopped_and_released",f.activeRequest==nil and #f.stops==1 and f:pendingCount()==0 and f.toggle.Text=="録画待機 ON",f:summary())
    f:advance(6);f:cue(10,3,"EGG_DELIVER")
    observe(name,"fresh_cue_after_release",f:requestsFrom(3)==1 and f:pendingCount()==1,f:summary())
    f:resolvePending("Success","CapturingAlready")
    f:advance(15);f:complete(3,"Success")
    observe(name,"fresh_clip_saves",f:promptsFrom(3)==1 and f.activeRequest==nil,f:summary())
    f:finish()
end

do
    local name="cancelled_clip_after_rearm"
    local f=newFixture(name,false)
    f:toggleConsent();f:cue(10,1,"EGG_STEAL")
    f:resolvePending("Success","CapturingAlready")
    f:advance(.1);f:toggleConsent()
    observe(name,"off_stops",#f.stops==1 and f.activeRequest==nil,f:summary())
    f:advance(.2);f:toggleConsent()
    f:complete(1,"Success")
    observe(name,"old_clip_not_reauthorized",f:promptsFrom(1)==0,f:summary())
    f:advance(3);f:cue(10,2,"EGG_DELIVER")
    f:resolvePending("Success","CapturingAlready")
    f:advance(12);f:complete(2,"Success")
    observe(name,"new_consent_clip_saves",f:promptsFrom(2)==1 and f.activeRequest==nil,f:summary())
    f:finish()
end

do
    local name="start_failures_release"
    local f=newFixture(name,false)
    f:toggleConsent();f:cue(10,1,"EGG_STEAL")
    f:advance(.1);f:resolvePending("OtherError","CapturingAlready")
    observe(name,"current_other_error_release",f:pendingCount()==0 and f.activeRequest==nil and #f.stops==0 and f.toggle.Text=="録画待機 ON",f:summary())
    f:advance(3);f:cue(10,2,"EGG_STEAL")
    f:advance(3.1);f:cue(11,3,"EGG_DELIVER")
    f:advance(3.2);f:resolvePending("NoDeviceSupport","CapturingAlready")
    observe(name,"stale_no_device_release",f:pendingCount()==0 and f.activeRequest==nil and #f.stops==0 and f.toggle.Text=="録画待機 ON",f:summary())
    f:advance(6);f:cue(11,4,"EGG_DELIVER")
    observe(name,"failure_retry_can_start",f:requestsFrom(4)==1 and f:pendingCount()==1,f:summary())
    f:resolvePending("Success","CapturingAlready")
    f:advance(15);f:complete(4,"Success")
    observe(name,"failure_retry_saves",f:promptsFrom(4)==1 and f.activeRequest==nil,f:summary())
    f:finish()
end

do
    local name="epoch_stop_sync_completion"
    local f=newFixture(name,true)
    f:toggleConsent();f:cue(10,1,"EGG_STEAL")
    f:resolvePending("Success","CapturingAlready")
    f:advance(3);f:cue(11,2,"EGG_DELIVER")
    observe(name,"synchronous_old_completion_fenced",f:promptsFrom(1)==0 and #f.stops==1,f:summary())
    observe(name,"new_epoch_request_pending",f:requestsFrom(2)==1 and f:pendingCount()==1,f:summary())
    f:resolvePending("Success","CapturingAlready")
    f:advance(12)
    observe(name,"normal_sync_stop_still_saves",f:promptsFrom(2)==1 and f.activeRequest==nil,f:summary())
    f:finish()
end

local pass,red=0,0
for _,entry in ipairs(observations) do if entry.passed then pass+=1 else red+=1 end end
print("TOTAL\t"..#observations.."\tPASS="..pass.."\tRED="..red)
