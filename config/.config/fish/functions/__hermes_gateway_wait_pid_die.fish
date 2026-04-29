function __hermes_gateway_wait_pid_die --description 'Wait for hermes gateway PID to exit before bootout/bootstrap'
    # `command hermes gateway stop` は SIGTERM を送って即 return するため、drain 完了
    # (最大 60s) 前に bootout/bootstrap すると、launchd の KeepAlive が新 process を
    # 多重 spawn しつつ旧 process は SIGKILL される。in-flight な write tx と相まって
    # state.db が破損する（4/26 の一次破損）。本関数は旧 PID が消えるまで待つ。

    set -l max_wait $argv[1]
    test -z "$max_wait"; and set max_wait 90

    set -l state_file ~/.hermes/gateway_state.json
    if not test -f $state_file
        return 0
    end

    set -l pid (jq -r '.pid // empty' $state_file 2>/dev/null)
    if test -z "$pid"; or test "$pid" = "null"
        return 0
    end

    if not kill -0 $pid 2>/dev/null
        return 0
    end

    set -l deadline (math (date +%s) + $max_wait)
    while test (date +%s) -lt $deadline
        if not kill -0 $pid 2>/dev/null
            return 0
        end
        sleep 0.5
    end

    set_color yellow
    echo "hermes-gateway: PID $pid still alive after $max_wait s — proceeding anyway" >&2
    set_color normal
    return 0
end
