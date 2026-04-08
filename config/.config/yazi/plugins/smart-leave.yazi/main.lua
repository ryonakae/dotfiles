--- Yazi起動時のディレクトリより上への移動をブロックし、H/Shift+Leftでのみ許可する
local get_state = ya.sync(function(state)
  return state.boot_cwd, tostring(cx.active.current.cwd)
end)

return {
  setup = function(state)
    state.boot_cwd = nil

    ps.sub("cd", function()
      if not state.boot_cwd then
        state.boot_cwd = tostring(cx.active.current.cwd)
      end
    end)
  end,

  entry = function()
    local boot, current = get_state()

    if not boot or current == boot then
      ya.notify {
        title = "smart-leave",
        content = "Already at the startup directory.\nPress Shift + H or Shift + ← to go up.",
        level = "warn",
        timeout = 3,
      }
      return
    end

    ya.emit("leave", {})
  end,
}
