function hermes-gateway --description "Manage hermes gateway (launchd + safehouse)"
    set -lx HERMES_HOME "$HOME/.hermes"
    set -l domain gui/(id -u)
    set -l label ai.hermes.gateway
    set -l plist "$HOME/Library/LaunchAgents/$label.plist"

    if test (count $argv) -ne 1
        echo "Usage: hermes-gateway {start|stop|restart|status|update}" >&2
        return 2
    end

    if contains -- "$argv[1]" start stop restart
        set -l manager (command launchctl managername)
        or return $status
        if test "$manager" != Aqua
            echo "hermes-gateway: run service operations from the user GUI session" >&2
            return 1
        end
    end

    switch "$argv[1]"
        case start
            if not test -d "$HOME/.hermes"
                echo "hermes-gateway: existing Hermes HOME is required: $HOME/.hermes" >&2
                return 1
            end
            command mkdir -p "$HOME/.hermes/logs"
            or return $status

            set_color cyan; echo "→ starting launchd service"; set_color normal
            command launchctl enable $domain/$label
            or return $status
            command launchctl bootstrap $domain "$plist"
            or return $status
            set_color green; echo "✓ gateway started"; set_color normal
        case stop
            set_color cyan; echo "→ requesting native gateway shutdown"; set_color normal
            command "$HOME/.local/libexec/hermes" --profile default gateway stop
            or return $status

            # Native gateway stop may already have unloaded the launchd job.
            set -l jobs (command launchctl list)
            set -l list_status $status
            if test $list_status -ne 0
                echo "hermes-gateway: launchctl list failed; service state is unknown" >&2
                return $list_status
            end
            if not string match -rq '^PID\s+Status\s+Label$' -- "$jobs[1]"
                echo "hermes-gateway: unknown launchctl list format" >&2
                return 1
            end
            if string match -rq '\sai\.hermes\.gateway$' -- $jobs
                command launchctl bootout $domain/$label
                or return $status
            end
            command launchctl disable $domain/$label
            or return $status
            set_color green; echo "✓ gateway stopped"; set_color normal
        case restart
            hermes-gateway stop
            or return $status
            hermes-gateway start
            return $status
        case status
            command "$HOME/.local/libexec/hermes" --profile default gateway status
            set -l native_status $status
            command launchctl print $domain/$label
            set -l launchd_status $status
            if test $native_status -ne 0
                return $native_status
            end
            return $launchd_status
        case update
            echo "Hermes is managed by Nix; no service was stopped or updated." >&2
            echo "In the dotfiles repository: scripts/dotfiles.sh update hermes-agent; then scripts/dotfiles.sh build." >&2
            echo "Apply the reviewed generation only after both services are safely stopped; restart explicitly after approval." >&2
            return 1
        case '*'
            echo "Usage: hermes-gateway {start|stop|restart|status|update}" >&2
            return 2
    end
end
