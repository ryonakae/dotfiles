local types = hs.eventtap.event.types
local buttonNumber = hs.eventtap.event.properties.mouseEventButtonNumber

local fingers = 0
-- The matching drag and up events must follow the action chosen at mouse down.
local pending

local function asMiddle(event, eventType)
  local middle = event:copy():setType(eventType)
  middle:setProperty(buttonNumber, 2)
  return middle
end

-- Globals keep the taps from being garbage collected.
touchTap = hs.eventtap.new({ types.gesture }, function(event)
  if event:getType(true) ~= types.gesture then
    return false
  end
  local count = 0
  for _, touch in ipairs(event:getTouches() or {}) do
    if touch.touching then
      count = count + 1
    end
  end
  fingers = count
  -- Swallowing gestures would break the native swipe gestures.
  return false
end)

clickTap = hs.eventtap.new({ types.leftMouseDown, types.leftMouseDragged, types.leftMouseUp }, function(event)
  local eventType = event:getType()
  if eventType == types.leftMouseDown then
    if fingers == 4 then
      pending = "close"
      -- Separate modifier key events lose their flags when posted from a tap, so set them on the key itself.
      return true, {
        hs.eventtap.event.newKeyEvent({ "cmd" }, "w", true),
        hs.eventtap.event.newKeyEvent({ "cmd" }, "w", false),
      }
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
