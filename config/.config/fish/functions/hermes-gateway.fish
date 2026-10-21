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
        command launchctl print $domain >/dev/null
        or begin
            echo "hermes-gateway: cannot inspect GUI domain $domain; service state is unknown" >&2
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
            __hermes_bootstrap $domain $label "$plist"
            or return $status
            set_color green; echo "✓ gateway started"; set_color normal
        case stop
            command launchctl print $domain/$label >/dev/null
            set -l query_status $status
            if test $query_status -ne 0; and test $query_status -ne 113
                echo "hermes-gateway: cannot inspect GUI service; state is unknown" >&2
                return $query_status
            end
            set -l native_launchctl "$HOME/.local/libexec/hermes-gui-launchctl/launchctl"
            if not test -x "$native_launchctl"
                echo "hermes-gateway: GUI-only native launchctl adapter is required" >&2
                return 1
            end
            set_color cyan; echo "→ requesting native gateway shutdown"; set_color normal
            begin
                set -lx PATH (path dirname "$native_launchctl") $PATH
                command "$HOME/.local/libexec/hermes" --profile default gateway stop
                or return $status
            end

            # Native gateway stop may already have unloaded the GUI job.
            command launchctl print $domain/$label >/dev/null
            set query_status $status
            if test $query_status -eq 0
                command launchctl bootout $domain/$label
                or return $status
            else if test $query_status -ne 113
                echo "hermes-gateway: cannot inspect GUI service; state is unknown" >&2
                return $query_status
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
            set -l green ""
            set -l yellow ""
            set -l muted ""
            set -l reset ""
            set -l red ""
            set -l error_reset ""
            if isatty stdout
                set green (set_color green)
                set yellow (set_color yellow)
                set muted (set_color --dim)
                set reset (set_color normal)
            end
            if isatty stderr
                set red (set_color red)
                set error_reset (set_color normal)
            end
            set -l service (command launchctl print $domain/$label)
            set -l query_status $status
            if test $query_status -ne 0
                if test $query_status -eq 113
                    printf '%s%s%s\n' "$red" "Gateway: unavailable (not registered in $domain)" "$error_reset" >&2
                else
                    printf '%s%s%s\n' "$red" "Gateway: unavailable (launchctl query failed; state is unknown)" "$error_reset" >&2
                end
                return $query_status
            end

            set -l state (string match -rg '^\tstate = (.+)$' -- $service)
            set -l pid (string match -rg '^\tpid = ([1-9][0-9]*)$' -- $service)
            set -l program (string match -rg '^\tprogram = (.+)$' -- $service)
            if test (count $state) -ne 1; or test (count $program) -ne 1
                printf '%s%s%s\n' "$red" "Gateway: unknown (unrecognized launchctl output)" "$error_reset" >&2
                return 1
            end
            if test "$state" = running
                if test (count $pid) -ne 1
                    printf '%s%s%s\n' "$red" "Gateway: unknown (running service has no valid PID)" "$error_reset" >&2
                    return 1
                end
                printf '%sGateway:%s %srunning%s (PID %s)\n' "$muted" "$reset" "$green" "$reset" "$pid"
            else
                printf '%sGateway:%s %s%s%s\n' "$muted" "$reset" "$yellow" "$state" "$reset"
            end
            printf '%sProgram:%s %s\n' "$muted" "$reset" "$program"

            # Hermes の標準 plist とは異なるため、標準 status の比較・定型表示は使わない。
            set -l run_at_load (command plutil -extract RunAtLoad raw -expect bool -o - "$plist")
            or return $status
            set -l keep_alive (command plutil -extract KeepAlive raw -expect bool -o - "$plist")
            or return $status
            set -l disabled (command plutil -extract Disabled raw -expect bool -o - "$plist")
            or return $status
            set -l overrides (command launchctl print-disabled $domain)
            or return $status
            if not string match -rq '^\s*disabled services = \{$' -- $overrides
                printf '%s%s%s\n' "$red" "hermes-gateway: unknown launchctl print-disabled format" "$error_reset" >&2
                return 1
            end
            set -l override (string match -rg '^\s*"ai\.hermes\.gateway" => (.+)$' -- $overrides)
            if test (count $override) -gt 1
                printf '%s%s%s\n' "$red" "hermes-gateway: ambiguous launchd enablement" "$error_reset" >&2
                return 1
            end
            if test (count $override) -eq 1
                switch "$override"
                    case enabled false
                        set disabled false
                    case disabled true
                        set disabled true
                    case '*'
                        printf '%s%s%s\n' "$red" "hermes-gateway: unknown launchd enablement: $override" "$error_reset" >&2
                        return 1
                end
            end
            if test "$run_at_load" = true; and test "$disabled" = false
                printf '%sStart at login:%s enabled\n' "$muted" "$reset"
            else
                printf '%sStart at login:%s disabled\n' "$muted" "$reset"
            end
            if test "$keep_alive" = true
                printf '%sRestart on crash (plist):%s enabled\n' "$muted" "$reset"
            else
                printf '%sRestart on crash (plist):%s disabled\n' "$muted" "$reset"
            end
            test "$state" = running
        case update
            echo "Hermes is managed by mise; no service was stopped or updated." >&2
            echo "Stop active Hermes services before updating; the checkout is updated in place." >&2
            echo "Update explicitly: /opt/homebrew/bin/mise -C ~/dotfiles -E hermes run hermes:update" >&2
            echo "After success, start only the services you stopped with hermes-gateway start." >&2
            return 1
        case '*'
            echo "Usage: hermes-gateway {start|stop|restart|status|update}" >&2
            return 2
    end
end
