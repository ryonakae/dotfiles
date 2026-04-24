function hermes-gateway --description "Manage hermes gateway (launchd + safehouse)"
    set domain gui/(id -u)
    set plist ~/Library/LaunchAgents/ai.hermes.gateway.plist

    switch $argv[1]
        case start
            launchctl bootstrap $domain $plist
        case stop
            launchctl bootout $domain/ai.hermes.gateway
        case restart
            launchctl bootout $domain/ai.hermes.gateway 2>/dev/null
            launchctl bootstrap $domain $plist
        case status
            launchctl print $domain/ai.hermes.gateway
        case '' '*'
            echo "Usage: hermes-gateway {start|stop|restart|status}"
            return 1
    end
end
