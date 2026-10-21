local types = hs.eventtap.event.types
local buttonNumber = hs.eventtap.event.properties.mouseEventButtonNumber

local fingers = 0
-- The matching drag and up events must follow the action chosen at mouse down.
local pending
-- Fraction of the trackpad width, large enough that a three-finger click never counts as a swipe.
local swipeThreshold = 0.1
-- One swipe sends one key press until the fingers leave or change count.
local swipe

local function asMiddle(event, eventType)
  local middle = event:copy():setType(eventType)
  middle:setProperty(buttonNumber, 2)
  return middle
end

-- Separate modifier key events lose their flags when posted from a tap, so set them on the key itself.
local function keyPress(mods, key)
  return {
    hs.eventtap.event.newKeyEvent(mods, key, true),
    hs.eventtap.event.newKeyEvent(mods, key, false),
  }
end

-- Globals keep the taps from being garbage collected.
touchTap = hs.eventtap.new({ types.gesture }, function(event)
  if event:getType(true) ~= types.gesture then
    return false
  end
  local count, x, y = 0, 0, 0
  for _, touch in ipairs(event:getTouches() or {}) do
    if touch.touching and touch.normalizedPosition then
      count = count + 1
      x = x + touch.normalizedPosition.x
      y = y + touch.normalizedPosition.y
    end
  end
  fingers = count

  if count ~= 3 then
    swipe = nil
    return false
  end
  x, y = x / count, y / count
  if not swipe then
    swipe = { x = x, y = y }
    return false
  end
  local dx, dy = x - swipe.x, y - swipe.y
  if swipe.done or math.abs(dx) < swipeThreshold or math.abs(dx) < math.abs(dy) then
    return false
  end
  swipe.done = true
  -- Swallowing gestures would break the native swipe gestures.
  if dx < 0 then
    return false, keyPress({ "ctrl" }, "tab")
  end
  return false, keyPress({ "ctrl", "shift" }, "tab")
end)

clickTap = hs.eventtap.new({ types.leftMouseDown, types.leftMouseDragged, types.leftMouseUp }, function(event)
  local eventType = event:getType()
  if eventType == types.leftMouseDown then
    if fingers == 4 then
      pending = "close"
      return true, keyPress({ "cmd" }, "w")
    elseif fingers == 3 then
      pending = "middle"
      return true, { asMiddle(event, types.otherMouseDown) }
    end
    pending = nil
    return false
  end

  local action = pending
  if eventType == types.leftMouseUp then
    pending = nil
  end
  if action == "close" then
    return true
  elseif action == "middle" then
    local middleType = eventType == types.leftMouseUp and types.otherMouseUp or types.otherMouseDragged
    return true, { asMiddle(event, middleType) }
  end
  return false
end)

touchTap:start()
clickTap:start()
