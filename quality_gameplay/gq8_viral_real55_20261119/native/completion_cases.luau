-- Add only two cases to the unchanged generic fixture.
-- Completion is delivered AFTER Start returned Success, never while pending.
-- Model the platform ending its active recording before issuing completion.
-- The error completion carries no VideoCapture, as the public callback contract
-- only provides a video handle on success. This is a controlled API schedule.
local function completeSpontaneousError(f,resultName)
    local request=assert(f.activeRequest,"no active recording to complete")
    assert(request.resolved and request.result.Name=="Success")
    f.activeRequest=nil
    request.capture=nil
    f:event("PLATFORM_RECORDING_ENDED","cue="..request.cue.seq..",result="..resultName)
    f:completeRequest(request,resultName)
end

for _,resultName in ipairs({"ScreenSizeChanged","OtherError"}) do
    local name="spontaneous_completion_"..resultName
    local f=newFixture(name,false)
    f:toggleConsent();f:cue(10,1,"EGG_STEAL")
    f:resolvePending("Success","CapturingAlready")
    observe(name,"successful_start_before_completion",f:activeSeq()==1 and f.toggle.Text=="● 録画中",f:summary())
    f:advance(1)
    completeSpontaneousError(f,resultName)
    observe(name,"platform_ended_without_source_stop",f.activeRequest==nil and #f.stops==0 and f:pendingCount()==0,f:summary())
    observe(name,"completion_retires_recording_ui",f.toggle.Text=="録画待機 ON",f:summary())
    observe(name,"error_completion_does_not_prompt_save",#f.prompts==0,f:summary())
    f:advance(3);f:cue(10,2,"EGG_DELIVER")
    observe(name,"eligible_next_cue_can_start",f:requestsFrom(2)==1 and f:pendingCount()==1,f:summary())
    -- A future repair may admit cue2. Resolve it normally so the remainder of
    -- this same contract does not intentionally strand an admitted API call.
    if f:pendingCount()>0 then
        f:resolvePending("Success","CapturingAlready")
        f:advance(12);f:complete(2,"Success")
    end
    f:advance(14.999)
    f:event("BEFORE_ORIGINAL_15S_DEADLINE",f:summary())
    f:advance(15)
    observe(name,"ready_by_original_timer_deadline",f.activeRequest==nil and f:pendingCount()==0 and f.toggle.Text=="録画待機 ON",f:summary())
    f:advance(18);f:cue(10,3,"EGG_DELIVER")
    observe(name,"cue_after_deadline_can_start",f:requestsFrom(3)==1 and f:pendingCount()==1,f:summary())
    f:resolvePending("Success","CapturingAlready")
    f:advance(27);f:complete(3,"Success")
    observe(name,"later_normal_stop_and_save_preserved",f:promptsFrom(3)==1 and f.activeRequest==nil and f.toggle.Text=="録画待機 ON",f:summary())
    f:finish()
end

local pass,red=0,0
for _,entry in ipairs(observations) do if entry.passed then pass+=1 else red+=1 end end
print("TOTAL\t"..#observations.."\tPASS="..pass.."\tRED="..red)
