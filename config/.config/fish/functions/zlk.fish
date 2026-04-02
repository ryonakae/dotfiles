function zlk --description "Kill the Zellij session for the current directory"
    if not command -q zellij
        echo "error: zellij command not found."
        return 127
    end

    set -l session (basename (pwd))
    set -l sessions (zellij list-sessions --short 2>/dev/null)

    if not contains -- $session $sessions
        echo "No Zellij session found for '$session'."
        return 1
    end

    read -P "Kill Zellij session '$session'? [y/N] " -l answer
    if not string match -qr '^[Yy]$' -- "$answer"
        echo "Cancelled."
        return 0
    end

    zellij delete-session -f "$session"
    set -l status_code $status

    if test $status_code -eq 0
        echo "Deleted Zellij session '$session'."
    end

    return $status_code
end
