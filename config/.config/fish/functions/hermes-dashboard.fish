function hermes-dashboard --description "Manage hermes dashboard (launchd + safehouse)"
    set -lx HERMES_HOME "$HOME/.hermes"
    set -l domain gui/(id -u)
    set -l label ai.hermes.dashboard
    set -l plist "$HOME/Library/LaunchAgents/$label.plist"
    set -l dashboard_host 0.0.0.0
    set -l dashboard_port 9120
    set -l local_url http://127.0.0.1:$dashboard_port

    if test (count $argv) -ne 1
        echo "Usage: hermes-dashboard {start|stop|restart|status|open|update}" >&2
        return 2
    end

    if contains -- "$argv[1]" start stop restart
        set -l manager (command launchctl managername)
        or return $status
        if test "$manager" != Aqua
            echo "hermes-dashboard: run service operations from the user GUI session" >&2
            return 1
        end
    end

    switch "$argv[1]"
        case start
            if not test -d "$HOME/.hermes"
                echo "hermes-dashboard: existing Hermes HOME is required: $HOME/.hermes" >&2
                return 1
            end
            command mkdir -p "$HOME/.hermes/logs"
            or return $status

            set_color cyan; echo "→ configuring dashboard bind: $dashboard_host:$dashboard_port"; set_color normal
            command launchctl setenv HERMES_DASHBOARD_HOST $dashboard_host
            or return $status
            command launchctl setenv HERMES_DASHBOARD_PORT $dashboard_port
            or return $status
            set_color cyan; echo "→ starting launchd service"; set_color normal
            command launchctl enable $domain/$label
            or return $status
            command launchctl bootstrap $domain "$plist"
            or return $status
            set_color green; echo "✓ dashboard started"; set_color normal
        case stop
            set_color cyan; echo "→ requesting native dashboard shutdown"; set_color normal
            command hermes --profile default dashboard --stop
            or return $status

            set -l jobs (command launchctl list)
            set -l list_status $status
            if test $list_status -ne 0
                echo "hermes-dashboard: launchctl list failed; service state is unknown" >&2
                return $list_status
            end
            if not string match -rq '^PID\s+Status\s+Label$' -- "$jobs[1]"
                echo "hermes-dashboard: unknown launchctl list format" >&2
                return 1
            end
            if string match -rq '\sai\.hermes\.dashboard$' -- $jobs
                command launchctl bootout $domain/$label
                or return $status
            end
            command launchctl disable $domain/$label
            or return $status
            set_color green; echo "✓ dashboard stopped"; set_color normal
        case restart
            hermes-dashboard stop
            or return $status
            hermes-dashboard start
            return $status
        case status
            echo "Local dashboard: $local_url"
            command hermes --profile default dashboard --status
            set -l native_status $status
            command launchctl print $domain/$label
            set -l launchd_status $status
            if test $native_status -ne 0
                return $native_status
            end
            return $launchd_status
        case open
            command open "$local_url"
            return $status
        case update
            echo "Hermes is managed by Nix; no service was stopped or updated." >&2
            echo "In the dotfiles repository: scripts/dotfiles.sh update hermes-agent; then scripts/dotfiles.sh build." >&2
            echo "Apply the reviewed generation only after both services are safely stopped; restart explicitly after approval." >&2
            return 1
        case '*'
            echo "Usage: hermes-dashboard {start|stop|restart|status|open|update}" >&2
            return 2
    end
end
