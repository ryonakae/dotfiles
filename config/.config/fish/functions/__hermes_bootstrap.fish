function __hermes_bootstrap --argument-names domain label plist
    for attempt in 1 2 3 4 5
        command launchctl bootstrap "$domain" "$plist"
        set -l bootstrap_status $status
        if test $bootstrap_status -eq 0
            return 0
        end
        if test $bootstrap_status -ne 5; or test $attempt -eq 5
            return $bootstrap_status
        end

        # bootout can return before launchd finishes removing the old registration.
        command launchctl print "$domain/$label" >/dev/null 2>&1
        set -l query_status $status
        if test $query_status -eq 0
            return $bootstrap_status
        else if test $query_status -ne 113
            echo "Hermes: cannot inspect $domain/$label after bootstrap failure" >&2
            return $query_status
        end
        command launchctl print "$domain" >/dev/null
        or return $status
        echo "→ launchd registration pending; retrying bootstrap ($attempt/4)" >&2
        command sleep 1
        or return $status
    end
end
