function __zellij_apply_dev_desktop --description "Apply Desktop swap layout to the initial tabs of a new dev session"
    if not command -q jq
        return 0
    end

    set -l session $argv[1]
    test -z "$session" && return 0
    set -l shells_done 0
    set -l tools_done 0

    for _ in (seq 1 50)
        set -l tabs_json (zellij --session "$session" action list-tabs --json --all 2>/dev/null)

        if test $shells_done -eq 0
            set -l shells_tab_id (printf '%s\n' "$tabs_json" | jq -r '.[] | select(.name == "Shells") | .tab_id' | head -n 1)
            if test -n "$shells_tab_id" -a "$shells_tab_id" != "null"
                zellij --session "$session" action next-swap-layout --tab-id "$shells_tab_id" >/dev/null 2>&1
                set shells_done 1
            end
        end

        if test $tools_done -eq 0
            set -l tools_tab_id (printf '%s\n' "$tabs_json" | jq -r '.[] | select(.name == "Tools") | .tab_id' | head -n 1)
            if test -n "$tools_tab_id" -a "$tools_tab_id" != "null"
                zellij --session "$session" action next-swap-layout --tab-id "$tools_tab_id" >/dev/null 2>&1
                set tools_done 1
            end
        end

        if test $shells_done -eq 1 -a $tools_done -eq 1
            return 0
        end
        sleep 0.1
    end

    return 0
end
