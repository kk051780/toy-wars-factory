-- Generic yielding CaptureService / client-GUI API fixture.
-- All game decisions execute from the one byte-exact body at the marker below.
local observations = {}
local function observe(case, name, passed, detail)
    table.insert(observations, {case=case,name=name,passed=passed,detail=detail})
    print("OBS\t"..case.."\t"..name.."\t"..(if passed then "PASS" else "RED").."\t"..detail)
end

local function signal()
    local handlers={}
    return {
        Connect=function(self,callback)
            table.insert(handlers,callback)
            return {Disconnect=function() end}
        end,
        Fire=function(self,...)
            for _,callback in ipairs(handlers) do callback(...) end
        end,
    }
end

local function enumItem(enumName,name,value)
    return {EnumType=enumName,Name=name,Value=value}
end

local function newFixture(case, synchronousCompletionOnStop)
    local f={case=case,now=0,requests={},stops={},prompts={},timers={},activeRequest=nil,nodes={}}
    local attrs,signals={},{}
    local currentCue={epoch=-1,seq=-1,kind=""}
    local playerGui={Name="PlayerGui"}
    local player={Character=nil}
    function player:WaitForChild(name) assert(name=="PlayerGui");return playerGui end
    function player:GetAttribute(name) return attrs[name] end
    function player:GetAttributeChangedSignal(name)
        if not signals[name] then signals[name]=signal() end
        return signals[name]
    end
    -- Public SDK enum member names; symbolic fixture objects preserve enum identity.
    local Enum={
        Font={GothamBold="GothamBold"},
        VideoCaptureStartedResult={
            Success=enumItem("VideoCaptureStartedResult","Success",0),
            OtherError=enumItem("VideoCaptureStartedResult","OtherError",1),
            CapturingAlready=enumItem("VideoCaptureStartedResult","CapturingAlready",2),
            NoDeviceSupport=enumItem("VideoCaptureStartedResult","NoDeviceSupport",3),
            NoSpaceOnDevice=enumItem("VideoCaptureStartedResult","NoSpaceOnDevice",4),
        },
        VideoCaptureResult={
            Success=enumItem("VideoCaptureResult","Success",0),
            OtherError=enumItem("VideoCaptureResult","OtherError",1),
            ScreenSizeChanged=enumItem("VideoCaptureResult","ScreenSizeChanged",2),
            TimeLimitReached=enumItem("VideoCaptureResult","TimeLimitReached",3),
        },
    }
    function f:event(kind,detail)
        print("EVT\t"..self.case.."\t"..tostring(self.now).."\t"..kind.."\t"..detail)
    end
    function f:pendingCount()
        local n=0
        for _,request in ipairs(self.requests) do if not request.resolved then n+=1 end end
        return n
    end
    function f:requestsFrom(seq)
        local n=0
        for _,request in ipairs(self.requests) do if request.cue.seq==seq then n+=1 end end
        return n
    end
    function f:promptsFrom(seq)
        local n=0
        for _,prompt in ipairs(self.prompts) do if prompt.capture.cueSeq==seq then n+=1 end end
        return n
    end
    function f:activeSeq() return self.activeRequest and self.activeRequest.cue.seq or -1 end
    function f:completeRequest(request,resultName)
        assert(request.resolved and request.result.Name=="Success")
        assert(not request.completed,"duplicate fixture completion")
        request.completed=true
        self:event("COMPLETE","cue="..request.cue.seq..",result="..resultName)
        request.callback(Enum.VideoCaptureResult[resultName],request.capture)
    end
    function f:complete(seq,resultName)
        local count=0
        for _,request in ipairs(self.requests) do
            if request.cue.seq==seq and request.resolved and request.result.Name=="Success" then
                count+=1;self:completeRequest(request,resultName)
            end
        end
        self:event("DELIVER_COMPLETION","cue="..seq..",matched="..count)
    end
    -- Conditional API ordering model only: no public ordering guarantee asserted.
    -- Expose completion through the same genuine enum objects as the base fixture.
    function f:completeBeforeStartReturn(seq,resultName)
        local target=nil
        for _,request in ipairs(self.requests) do
            if request.cue.seq==seq and not request.resolved then
                assert(target==nil,"multiple pending requests for conditional completion")
                target=request
            end
        end
        local request=assert(target,"missing pending request")
        assert(not request.completed,"duplicate conditional completion")
        local outcome=assert(Enum.VideoCaptureResult[resultName],resultName)
        request.completed=true
        if outcome==Enum.VideoCaptureResult.Success or outcome==Enum.VideoCaptureResult.TimeLimitReached then
            request.capture={Name="API_VIDEO_CAPTURE_HANDLE",cueSeq=request.cue.seq}
        else
            request.capture=nil
        end
        if self.activeRequest==request then self.activeRequest=nil end
        self:event("COMPLETE_BEFORE_START_RETURN","cue="..seq..",result="..resultName)
        request.callback(outcome,request.capture)
    end

    local CaptureService={}
    function CaptureService:StartVideoCaptureAsync(callback,params)
        assert(type(callback)=="function" and type(params)=="table")
        local request={
            thread=coroutine.running(),callback=callback,cue=table.clone(currentCue),
            resolved=false,completed=false,overlap=f:pendingCount()>0 or f.activeRequest~=nil,
        }
        table.insert(f.requests,request)
        f:event("START","cue="..request.cue.seq..",pending="..f:pendingCount()..",overlap="..tostring(request.overlap))
        return coroutine.yield("WAITING_CAPTURE_START")
    end
    function CaptureService:StopVideoCapture()
        local active=f.activeRequest
        table.insert(f.stops,{at=f.now,cueSeq=active and active.cue.seq or -1})
        f.activeRequest=nil
        f:event("STOP","cue="..(active and active.cue.seq or -1))
        if synchronousCompletionOnStop and active and not active.completed then
            f:completeRequest(active,"Success")
        end
    end
    function CaptureService:PromptSaveCapturesToGallery(captures,callback)
        assert(type(captures)=="table" and #captures==1 and type(callback)=="function")
        table.insert(f.prompts,{at=f.now,capture=captures[1]})
        f:event("PROMPT","cue="..captures[1].cueSeq)
        callback({[captures[1]]=false}) -- prompt delivery, not actual accepted/saved video
    end
    local services={
        Players={LocalPlayer=player},CaptureService=CaptureService,TweenService={},
        RunService={IsStudio=function() return true end},
    }
    local game={GetService=function(self,name) assert(services[name],name);return services[name] end}
    local Instance={new=function(className)
        assert(className=="ScreenGui" or className=="TextButton" or className=="UICorner",className)
        local node={ClassName=className}
        if className=="TextButton" then node.Activated=signal();f.toggle=node end
        table.insert(f.nodes,node)
        return node
    end}
    local Color3={fromRGB=function(r,g,b) return {r=r,g=g,b=b} end}
    local UDim2={fromOffset=function(x,y) return {x=x,y=y} end,new=function(...) return {...} end}
    local UDim={new=function(...) return {...} end}
    local Vector2={new=function(...) return {...} end}
    local task={}
    function task.spawn(callback)
        local thread=coroutine.create(callback)
        local ok,result=coroutine.resume(thread)
        assert(ok,result)
        return thread
    end
    function task.delay(seconds,callback)
        table.insert(f.timers,{at=f.now+seconds,callback=callback})
    end
    local time=function() return f.now end
    function f:advance(now)
        assert(now>=self.now)
        while true do
            local index,earliest=nil,math.huge
            for i,timer in ipairs(self.timers) do
                if timer.at<=now and timer.at<earliest then index=i;earliest=timer.at end
            end
            if not index then break end
            self.now=earliest
            table.remove(self.timers,index).callback()
        end
        self.now=now
    end
    function f:toggleConsent()
        self:event("TOGGLE","before="..self.toggle.Text)
        self.toggle.Activated:Fire()
    end
    function f:cue(epoch,seq,kind)
        currentCue={epoch=epoch,seq=seq,kind=kind}
        self:event("CUE","epoch="..epoch..",seq="..seq..",kind="..kind)
        -- Real Host publishes kind, epoch and finally monotone seq.
        attrs.EGGRUMBLE_ViralKind=kind
        attrs.EGGRUMBLE_ViralEpoch=epoch
        attrs.EGGRUMBLE_ViralSeq=seq
        signals.EGGRUMBLE_ViralSeq:Fire()
    end
    function f:resolvePending(resultName,overlapResultName)
        local pending={}
        for _,request in ipairs(self.requests) do
            if not request.resolved then table.insert(pending,request) end
        end
        self:event("RESOLVE_BATCH","count="..#pending..",result="..resultName..",overlap="..overlapResultName)
        for _,request in ipairs(pending) do
            local name=if request.overlap then overlapResultName else resultName
            local result=Enum.VideoCaptureStartedResult[name]
            assert(result,name)
            request.resolved=true;request.result=result
            request.capture={Name="API_VIDEO_CAPTURE_HANDLE",cueSeq=request.cue.seq}
            if result==Enum.VideoCaptureStartedResult.Success and not request.completed then self.activeRequest=request end
            self:event("RETURN","cue="..request.cue.seq..",result="..name)
            local ok,detail=coroutine.resume(request.thread,result)
            assert(ok,detail)
            assert(coroutine.status(request.thread)=="dead")
        end
    end
    function f:summary()
        return "requests="..#self.requests..",pending="..self:pendingCount()..",stops="..#self.stops
            ..",prompts="..#self.prompts..",activeCue="..self:activeSeq()..",text="..self.toggle.Text
    end
    function f:finish()
        self:advance(30)
        assert(self:pendingCount()==0,"fixture left unresolved calls")
        assert(self.activeRequest==nil,"fixture left active recording")
        self:event("FINISH",self:summary())
    end
    local function executeFullClient()
-- __EXACT_FULL_CLIENT_BODY__
    end
    executeFullClient()
    return f
end
