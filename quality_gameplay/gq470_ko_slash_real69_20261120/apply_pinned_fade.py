"""Apply the exact #928 PC-tested fade after the original cap patch."""

import hashlib


CAP_SHA256 = "63e6658dd635588f71ffdb21a130b8b837f7862abfbe9d4eeb2f66e26638a8b8"
FADE_SHA256 = "4c4b8034f7a910ca310046771a3987f8559041b95be1706f0bff3602703be7ba"
INSTANT = b"""   {Size=Vector3.new(.8,3.5,.28),CFrame=endAt,Transparency=1})
  tween:Play()
  Debris:AddItem(fin,.30)
"""
DELAYED = b"""   {Size=Vector3.new(.8,3.5,.28),CFrame=endAt})
  -- Leave time for both fins to replicate before fading the KO confirmation.
  local fade=TweenService:Create(
   fin,TweenInfo.new(.18,Enum.EasingStyle.Linear,Enum.EasingDirection.Out,0,false,.31),
   {Transparency=1})
  tween:Play()
  fade:Play()
  Debris:AddItem(fin,.53)
"""


def replace_exact(raw, old, new, before, after):
    if hashlib.sha256(raw).hexdigest() != before or raw.count(old) != 1:
        raise ValueError("RED_KO_FADE_EXACT_PARENT")
    result = raw.replace(old, new, 1)
    if hashlib.sha256(result).hexdigest() != after:
        raise ValueError("RED_KO_FADE_EXACT_CHILD")
    return result


def transform(capped):
    return replace_exact(capped, INSTANT, DELAYED, CAP_SHA256, FADE_SHA256)


def inverse(selected):
    return replace_exact(selected, DELAYED, INSTANT, FADE_SHA256, CAP_SHA256)
