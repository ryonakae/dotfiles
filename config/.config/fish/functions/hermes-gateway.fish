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
            # `command hermes gateway stop` は SIGTERM 投げて即 return するので、bootout 前に
            # 旧 PID が drain を終えるまで待つ。これがないと launchd KeepAlive が多重 spawn し、
            # in-flight write tx と相まって state.db が破損する（4/26 の一次破損）。
            # safehouse 経由だと別 sandbox の launchd 配下 PID へ signal が通らないため command で迂回
            command hermes gateway stop
            __hermes_gateway_wait_pid_die 90
            if launchctl bootout $domain/ai.hermes.gateway
                set_color green; echo "hermes-gateway: stopped"; set_color normal
            else
                set_color red; echo "hermes-gateway: stop failed" >&2; set_color normal
                return 1
            end
        case restart
            command hermes gateway stop 2>/dev/null
            __hermes_gateway_wait_pid_die 90
            launchctl bootout $domain/ai.hermes.gateway 2>/dev/null
            if launchctl bootstrap $domain $plist
                set_color green; echo "hermes-gateway: restarted"; set_color normal
            else
                set_color red; echo "hermes-gateway: restart failed" >&2; set_color normal
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
            echo "Usage: hermes-gateway {start|stop|restart|status|update [hermes-update-args...]}"
            return 1
    end
end
