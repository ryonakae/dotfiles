function hermes-dashboard --description "Manage hermes dashboard (launchd + safehouse)"
    set domain gui/(id -u)
    set label ai.hermes.dashboard
    set plist ~/Library/LaunchAgents/ai.hermes.dashboard.plist
    set dashboard_host ryo-mac-mini.tail818984.ts.net
    set dashboard_port 9119
    set url http://$dashboard_host:$dashboard_port

    switch $argv[1]
        case start
            set_color cyan; echo "→ configuring dashboard host: $dashboard_host:$dashboard_port"; set_color normal
            launchctl setenv HERMES_DASHBOARD_HOST $dashboard_host
            launchctl setenv HERMES_DASHBOARD_PORT $dashboard_port
            set_color cyan; echo "→ starting launchd service"; set_color normal
            if launchctl bootstrap $domain $plist
                set_color green; echo "✓ dashboard started"; set_color normal
            else
                set_color red; echo "✗ dashboard start failed" >&2; set_color normal
                return 1
            end
        case stop
            set_color cyan; echo "→ requesting graceful dashboard shutdown"; set_color normal
            set -l stop_out (command hermes dashboard --stop 2>&1)
            set -l stop_status $status
            if test $stop_status -ne 0
                set_color yellow; echo "! dashboard stop command returned rc=$stop_status" >&2; set_color normal
                test -n "$stop_out"; and printf '%s\n' $stop_out | string replace -r '^' '  '
            end

            set_color cyan; echo "→ waiting for dashboard port to close"; set_color normal
            set -l deadline (math (date +%s) + 30)
            while test (date +%s) -lt $deadline
                if not lsof -nP -iTCP:9119 -sTCP:LISTEN >/dev/null 2>&1
                    break
                end
                sleep 0.5
            end

            set_color cyan; echo "→ unloading launchd service"; set_color normal
            set -l bootout_out (launchctl bootout $domain/$label 2>&1)
            set -l bootout_status $status
            if test $bootout_status -eq 0
                set_color green; echo "✓ dashboard stopped"; set_color normal
            else if test $bootout_status -eq 3; or test $bootout_status -eq 113; or string match -q '*No such process*' -- "$bootout_out"; or string match -q '*Could not find service*' -- "$bootout_out"
                set_color blue; echo "• launchd service was already unloaded"; set_color normal
            else
                set_color red; echo "✗ dashboard stop failed (rc=$bootout_status)" >&2; set_color normal
                test -n "$bootout_out"; and printf '%s\n' $bootout_out | string replace -r '^' '  '
                return 1
            end
        case restart
            set_color cyan; echo "→ requesting graceful dashboard shutdown"; set_color normal
            set -l stop_out (command hermes dashboard --stop 2>&1)
            set -l stop_status $status
            if test $stop_status -ne 0
                set_color yellow; echo "! dashboard stop command returned rc=$stop_status" >&2; set_color normal
                test -n "$stop_out"; and printf '%s\n' $stop_out | string replace -r '^' '  '
            end

            set_color cyan; echo "→ waiting for dashboard port to close"; set_color normal
            set -l deadline (math (date +%s) + 30)
            while test (date +%s) -lt $deadline
                if not lsof -nP -iTCP:9119 -sTCP:LISTEN >/dev/null 2>&1
                    break
                end
                sleep 0.5
            end

            set_color cyan; echo "→ unloading launchd service"; set_color normal
            set -l bootout_out (launchctl bootout $domain/$label 2>&1)
            set -l bootout_status $status
            if test $bootout_status -eq 0
                set_color green; echo "✓ dashboard stopped"; set_color normal
            else if test $bootout_status -eq 3; or test $bootout_status -eq 113; or string match -q '*No such process*' -- "$bootout_out"; or string match -q '*Could not find service*' -- "$bootout_out"
                set_color blue; echo "• launchd service was already unloaded"; set_color normal
            else
                set_color yellow; echo "! launchd unload returned rc=$bootout_status" >&2; set_color normal
                test -n "$bootout_out"; and printf '%s\n' $bootout_out | string replace -r '^' '  '
                return 1
            end

            set_color cyan; echo "→ configuring dashboard host: $dashboard_host:$dashboard_port"; set_color normal
            launchctl setenv HERMES_DASHBOARD_HOST $dashboard_host
            launchctl setenv HERMES_DASHBOARD_PORT $dashboard_port
            set_color cyan; echo "→ starting launchd service"; set_color normal
            if launchctl bootstrap $domain $plist
                set_color green; echo "✓ dashboard started"; set_color normal
            else
                set_color red; echo "✗ dashboard restart failed during start" >&2; set_color normal
                return 1
            end
        case status
            set -l out (launchctl print $domain/$label 2>&1)
            set -l rc $status
            if test $rc -ne 0
                set_color red; echo "✗ launchctl print failed (rc=$rc)" >&2; set_color normal
                printf '%s\n' $out | string replace -r '^' '  '
                return 1
            else
                set state_line (printf '%s\n' $out | grep -E '^\s*state = ' | head -n 1 | string trim)
                set pid_line (printf '%s\n' $out | grep -E '^\s*pid = ' | head -n 1 | string trim)
                set exit_line (printf '%s\n' $out | grep -E '^\s*last exit code = ' | head -n 1 | string trim)
                set program_line (printf '%s\n' $out | grep -E '^\s*program = ' | head -n 1 | string trim)
                set runs_line (printf '%s\n' $out | grep -E '^\s*runs = ' | head -n 1 | string trim)

                set state_value (string replace -r '^state =\s*' '' -- "$state_line")
                set pid_value (string replace -r '^pid =\s*' '' -- "$pid_line")
                set exit_value (string replace -r '^last exit code =\s*' '' -- "$exit_line")
                set program_value (string replace -r '^program =\s*' '' -- "$program_line")
                set runs_value (string replace -r '^runs =\s*' '' -- "$runs_line")

                set_color blue; echo "• launchd"; set_color normal
                set_color blue; echo "• url: $url"; set_color normal
                if test "$state_value" = running
                    set_color green; echo "✓ state: $state_value"; set_color normal
                else if test -n "$state_value"
                    set_color yellow; echo "! state: $state_value" >&2; set_color normal
                else
                    set_color yellow; echo "! state: unknown" >&2; set_color normal
                end

                test -n "$pid_value"; and begin; set_color blue; echo "• launchd pid: $pid_value"; set_color normal; end
                test -n "$runs_value"; and begin; set_color blue; echo "• runs: $runs_value"; set_color normal; end
                if test -n "$program_value"
                    if string match -q '*/safe-hermes-dashboard.sh' -- "$program_value"
                        set_color green; echo "✓ wrapper: $program_value"; set_color normal
                    else
                        set_color yellow; echo "! wrapper: $program_value" >&2; set_color normal
                    end
                end
                if test -n "$exit_value"
                    if test "$exit_value" = 0; or test "$exit_value" = "(never exited)"
                        set_color blue; echo "• last exit: $exit_value"; set_color normal
                    else
                        set_color yellow; echo "! last exit: $exit_value" >&2; set_color normal
                    end
                end
            end

            echo
            set_color blue; echo "• hermes dashboard"; set_color normal
            command hermes dashboard --status 2>&1 | string replace -r '^' '  '

            if curl -fsS --max-time 3 $url/api/status >/dev/null 2>&1
                set_color green; echo "✓ HTTP: $url/api/status"; set_color normal
            else
                set_color yellow; echo "! HTTP not reachable: $url" >&2; set_color normal
            end
        case open
            open $url
        case '' '*'
            echo "Usage: hermes-dashboard {start|stop|restart|status|open}"
            return 1
    end
end
