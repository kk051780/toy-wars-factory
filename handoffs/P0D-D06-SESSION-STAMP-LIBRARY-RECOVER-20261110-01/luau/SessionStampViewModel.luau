-- Read-only result model for UI. Never sends internal round IDs or ledger to clients.
local ViewModel = {}
function ViewModel.fromRewardView(rewardView, receipt)
    assert(type(rewardView) == "table" and rewardView.sessionOnly == true)
    assert(type(receipt) == "table" and type(receipt.awarded) == "number")
    return {
        title = "FREE TRAP STAMPS",
        earnedThisMatch = receipt.awarded,
        totalStamps = rewardView.stamps,
        nextRewardAt = rewardView.nextRewardAt,
        toNextReward = rewardView.toNextReward,
        unlockedCosmetics = table.clone(rewardView.unlockedCosmetics),
        status = receipt.status,
        sessionOnly = true,
        saved = false,
        saveLabel = "This session only - not saved",
    }
end
return ViewModel
