function hermes-gateway --description "Manage hermes gateway (launchd + safehouse)"
    set domain gui/(id -u)
    set plist ~/Library/LaunchAgents/ai.hermes.gateway.plist

    switch $argv[1]
        case start
            if launchctl bootstrap $domain $plist
                set_color green; echo "hermes-gateway: started"; set_color normal
            else
                set_color red; echo "hermes-gateway: start failed" >&2; set_color normal
                return 1
            end
        case stop
            # bootout の SIGTERM/SIGKILL で DB が壊れないよう、先に正規シャットダウンを通す。
            # safehouse 経由だと別 sandbox の launchd 配下 PID へ signal が通らないため command で迂回
            command hermes gateway stop
            if launchctl bootout $domain/ai.hermes.gateway
                set_color green; echo "hermes-gateway: stopped"; set_color normal
            else
                set_color red; echo "hermes-gateway: stop failed" >&2; set_color normal
                return 1
            end
        case restart
            command hermes gateway stop 2>/dev/null
            launchctl bootout $domain/ai.hermes.gateway 2>/dev/null
            if launchctl bootstrap $domain $plist
                set_color green; echo "hermes-gateway: restarted"; set_color normal
            else
                set_color red; echo "hermes-gateway: restart failed" >&2; set_color normal
                return 1
            end
        case status
            set out (launchctl print $domain/ai.hermes.gateway 2>&1)
            set rc $status
            if test $rc -ne 0
                set_color red; echo "hermes-gateway: launchctl print failed (rc=$rc)"; set_color normal
                printf '%s\n' $out
                return 1
            end

            set state_line (printf '%s\n' $out | grep -E '^\s*state = ' | head -n 1 | string trim)
            set pid_line (printf '%s\n' $out | grep -E '^\s*pid = ' | head -n 1 | string trim)
            set exit_line (printf '%s\n' $out | grep -E '^\s*last exit code = ' | head -n 1 | string trim)

            echo "── launchd ──"
            echo "  $state_line"
            test -n "$pid_line"; and echo "  $pid_line"
            test -n "$exit_line"; and echo "  $exit_line"

            echo
            # safehouse 経由だと sandbox 由来で not loaded を誤検知するため command で迂回。
            # stale 警告は wrapper 置換構成のため恒久的に出るので無視してよい
            echo "── hermes gateway status (※ stale 警告は構造上残る。loaded か否かで判断) ──"
            command hermes gateway status
        case '' '*'
            echo "Usage: hermes-gateway {start|stop|restart|status}"
            return 1
    end
end
