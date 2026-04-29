function hermes-gateway --description "Manage hermes gateway (launchd + safehouse)"
    set domain gui/(id -u)
    set plist ~/Library/LaunchAgents/ai.hermes.gateway.plist

    switch $argv[1]
        case start
            set_color cyan; echo "→ starting launchd service"; set_color normal
            if launchctl bootstrap $domain $plist
                set_color green; echo "✓ gateway started"; set_color normal
            else
                set_color red; echo "✗ gateway start failed" >&2; set_color normal
                return 1
            end
        case stop
            # bootout の SIGTERM/SIGKILL で DB が壊れないよう、先に正規シャットダウンを通す。
            # `command hermes gateway stop` は SIGTERM 投げて即 return するので、bootout 前に
            # 旧 PID が drain を終えるまで待つ。これがないと launchd KeepAlive が多重 spawn し、
            # in-flight write tx と相まって state.db が破損する（4/26 の一次破損）。
            # safehouse 経由だと別 sandbox の launchd 配下 PID へ signal が通らないため command で迂回
            set_color cyan; echo "→ requesting graceful shutdown"; set_color normal
            set -l stop_out (command hermes gateway stop 2>&1)
            set -l stop_status $status
            if test $stop_status -ne 0
                set_color yellow; echo "! graceful shutdown command returned rc=$stop_status" >&2; set_color normal
                test -n "$stop_out"; and printf '%s\n' $stop_out | string replace -r '^' '  '
            end

            set_color cyan; echo "→ waiting for gateway process to exit"; set_color normal
            __hermes_gateway_wait_pid_die 90

            set_color cyan; echo "→ unloading launchd service"; set_color normal
            if launchctl bootout $domain/ai.hermes.gateway
                set_color green; echo "✓ gateway stopped"; set_color normal
            else
                set_color red; echo "✗ gateway stop failed" >&2; set_color normal
                return 1
            end
        case restart
            set_color cyan; echo "→ requesting graceful shutdown"; set_color normal
            set -l stop_out (command hermes gateway stop 2>&1)
            set -l stop_status $status
            if test $stop_status -ne 0
                set_color yellow; echo "! graceful shutdown command returned rc=$stop_status" >&2; set_color normal
                test -n "$stop_out"; and printf '%s\n' $stop_out | string replace -r '^' '  '
            end

            set_color cyan; echo "→ waiting for gateway process to exit"; set_color normal
            __hermes_gateway_wait_pid_die 90

            set_color cyan; echo "→ unloading launchd service"; set_color normal
            set -l bootout_out (launchctl bootout $domain/ai.hermes.gateway 2>&1)
            set -l bootout_status $status
            if test $bootout_status -eq 0
                set_color green; echo "✓ gateway stopped"; set_color normal
            else
                set_color blue; echo "• launchd unload skipped or service was already stopped"; set_color normal
                test -n "$bootout_out"; and printf '%s\n' $bootout_out | string replace -r '^' '  '
            end

            set_color cyan; echo "→ starting launchd service"; set_color normal
            if launchctl bootstrap $domain $plist
                set_color green; echo "✓ gateway started"; set_color normal
            else
                set_color red; echo "✗ gateway restart failed during start" >&2; set_color normal
                return 1
            end
        case update
            set -l update_args
            test (count $argv) -gt 1; and set update_args $argv[2..-1]

            # `--check` は git fetch して確認するだけで何もインストールしないので、
            # gateway を止める必要が無い。透過パスして即 return。
            if contains -- --check $update_args
                command hermes update $update_args
                return $status
            end

            # `hermes update` 単体だと、内部で動作中の gateway を drain (60s) → 駄目なら
            # launchctl で hard restart する。ここで in-flight write tx や schema migration と
            # 競合すると state.db が破損する（4/27 v10 trigram FTS migration race の遠因）。
            # 先に gateway を完全停止 → launchd から外しておくことで、`hermes update` 内部の
            # restart は無人状態で即 bootstrap になり、race window が消える。
            command hermes gateway stop
            __hermes_gateway_wait_pid_die 120
            launchctl bootout $domain/ai.hermes.gateway 2>/dev/null

            command hermes update $update_args
            set -l update_status $status

            # `hermes update` が gateway を bootstrap し直しているはずだが、未起動なら拾う。
            if not launchctl print $domain/ai.hermes.gateway >/dev/null 2>&1
                launchctl bootstrap $domain $plist 2>/dev/null
            end

            if test $update_status -ne 0
                set_color red; echo "hermes-gateway: update failed (gateway restored)" >&2; set_color normal
                return $update_status
            end
            set_color green; echo "hermes-gateway: updated"; set_color normal
        case status
            set out (launchctl print $domain/ai.hermes.gateway 2>&1)
            set rc $status
            if test $rc -ne 0
                set_color red; echo "✗ launchctl print failed (rc=$rc)" >&2; set_color normal
                printf '%s\n' $out | string replace -r '^' '  '
                return 1
            end

            set state_line (printf '%s\n' $out | grep -E '^\s*state = ' | head -n 1 | string trim)
            set pid_line (printf '%s\n' $out | grep -E '^\s*pid = ' | head -n 1 | string trim)
            set exit_line (printf '%s\n' $out | grep -E '^\s*last exit code = ' | head -n 1 | string trim)

            set state_value (string replace -r '^state =\s*' '' -- "$state_line")
            set pid_value (string replace -r '^pid =\s*' '' -- "$pid_line")
            set exit_value (string replace -r '^last exit code =\s*' '' -- "$exit_line")

            set_color blue; echo "• launchd"; set_color normal
            if test "$state_value" = running
                set_color green; echo "✓ state: $state_value"; set_color normal
            else if test -n "$state_value"
                set_color yellow; echo "! state: $state_value" >&2; set_color normal
            else
                set_color yellow; echo "! state: unknown" >&2; set_color normal
            end

            test -n "$pid_value"; and begin; set_color blue; echo "• pid: $pid_value"; set_color normal; end
            if test -n "$exit_value"
                if test "$exit_value" = 0; or test "$exit_value" = "(never exited)"
                    set_color blue; echo "• last exit code: $exit_value"; set_color normal
                else
                    set_color yellow; echo "! last exit code: $exit_value" >&2; set_color normal
                end
            end

            echo
            # safehouse 経由だと sandbox 由来で not loaded を誤検知するため command で迂回。
            # stale 警告は wrapper 置換構成のため恒久的に出るので、警告文は落として対処コマンドだけ残す。
            set status_out (command hermes gateway status 2>&1)
            set status_rc $status
            if test -n "$status_out"
                printf '%s\n' $status_out | while read -l line
                    set -l trimmed (string trim -- $line)
                    switch $trimmed
                        case '⚠ Service definition is stale relative to the current Hermes install'
                            continue
                        case 'Run:*'
                            printf '%s\n' $trimmed
                        case '✓*'
                            set_color green; printf '%s\n' $trimmed; set_color normal
                        case '⚠*'
                            set_color yellow; printf '%s\n' $trimmed; set_color normal
                        case '✗*' 'Error*' 'error*'
                            set_color red; printf '%s\n' $trimmed; set_color normal
                        case '*'
                            printf '%s\n' $line
                    end
                end
            end
            if test $status_rc -ne 0
                set_color yellow; echo "! hermes gateway status returned rc=$status_rc" >&2; set_color normal
            end
        case '' '*'
            echo "Usage: hermes-gateway {start|stop|restart|status|update [hermes-update-args...]}"
            return 1
    end
end
