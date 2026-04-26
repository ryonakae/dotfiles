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
            # bootout の SIGTERM/SIGKILL で DB が壊れないよう、先に正規シャットダウンを通す
            hermes gateway stop
            if launchctl bootout $domain/ai.hermes.gateway
                set_color green; echo "hermes-gateway: stopped"; set_color normal
            else
                set_color red; echo "hermes-gateway: stop failed" >&2; set_color normal
                return 1
            end
        case restart
            hermes gateway stop 2>/dev/null
            launchctl bootout $domain/ai.hermes.gateway 2>/dev/null
            if launchctl bootstrap $domain $plist
                set_color green; echo "hermes-gateway: restarted"; set_color normal
            else
                set_color red; echo "hermes-gateway: restart failed" >&2; set_color normal
                return 1
            end
        case status
            launchctl print $domain/ai.hermes.gateway
        case '' '*'
            echo "Usage: hermes-gateway {start|stop|restart|status}"
            return 1
    end
end
