function zlka --description "Kill selected Zellij sessions"
    if not command -q zellij
        echo "error: zellij command not found."
        return 127
    end

    if not command -q fzf
        echo "error: fzf command not found. Install it with: brew install fzf"
        return 127
    end

    set -l sessions (zellij list-sessions --short 2>/dev/null)

    if test -z "$sessions"
        echo "No active Zellij sessions found."
        return 1
    end

    set -l selected (string join \n $sessions | fzf \
        --with-shell "bash -c" \
        --multi \
        --layout=reverse-list \
        --border=rounded \
        --border-label=" Zellij Sessions " \
        --header="Space: toggle | Enter: delete selected | Esc: cancel" \
        --prompt="> " \
        --info=inline \
        --height=40% \
        --bind "space:toggle+down" \
        --bind "enter:transform:if [[ \$FZF_SELECT_COUNT -gt 0 ]]; then echo accept; else echo change-header:Select at least one session with Space.; fi")

    test $status -ne 0 && return
    test -z "$selected" && return

    echo "The following Zellij sessions will be deleted:"
    for session in $selected
        echo "  - $session"
    end

    read -P "Continue? [y/N] " -l answer
    if not string match -qr '^[Yy]$' -- "$answer"
        echo "Cancelled."
        return 0
    end

    set -l failed 0
    for session in $selected
        zellij delete-session -f "$session"
        or set failed 1
    end

    if test $failed -eq 0
        echo "Deleted selected Zellij sessions."
    end

    return $failed
end
