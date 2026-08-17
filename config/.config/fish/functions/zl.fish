function __zl_session_names
    command zellij list-sessions --short 2>/dev/null
end

function __zl_list
    set -l sessions (command zellij list-sessions --no-formatting); or return
    set -l tab (printf '\t')
    set -l running_status running
    set -l stopped_status stopped
    if test -t 1
        set running_status (printf '%s%s%s' (set_color green) running (set_color normal))
        set stopped_status (printf '%s%s%s' (set_color red) stopped (set_color normal))
    end
    set -l rows

    for session in $sessions
        set -l name (string replace -r ' \[Created .*$' '' -- "$session")
        set -l session_status $running_status
        string match -q '* (EXITED -*' -- "$session"; and set session_status $stopped_status
        set -a rows (string join "$tab" "$name" "$session_status")
    end

    printf '%s\n' (string join "$tab" name status) $rows | command column -t -s "$tab"
end

function __zl_attach --argument-names session
    if set -q ZELLIJ
        command zellij action switch-session -- "$session"
    else
        command zellij attach -- "$session"
    end
end

function __zl_open --argument-names path session
    if not test -d "$path"
        echo "error: directory not found: $path"
        return 1
    end

    set -l project_dir (realpath "$path")
    test -n "$session" || set session (basename "$project_dir")
    if string match -q '*/*' -- "$session"
        echo "error: '$session' is not a valid Zellij session name."
        return 2
    end

    if contains -- "$session" (__zl_session_names)
        __zl_attach "$session"
        return $status
    end

    if set -q ZELLIJ
        command zellij action switch-session -l dev -c "$project_dir" -- "$session"
    else
        command env -C "$project_dir" zellij -l dev attach -c -- "$session"
    end
end

function __zl_pick
    if not command -q fd
        echo "error: fd command not found. Install it with: brew install fd"
        return 127
    end
    if not command -q fzf
        echo "error: fzf command not found. Install it with: brew install fzf"
        return 127
    end

    set -l dev_dir "$HOME/dev"
    set -l history_file "$HOME/.cache/zl_history"
    set -l sessions (__zl_session_names)
    set -l sorted_sessions

    if test -f "$history_file" -a (count $sessions) -gt 0
        for name in (tail -r "$history_file" 2>/dev/null)
            if contains -- "$name" $sessions; and not contains -- "$name" $sorted_sessions
                set -a sorted_sessions "$name"
            end
        end
        for name in $sessions
            contains -- "$name" $sorted_sessions; or set -a sorted_sessions "$name"
        end
    else
        set sorted_sessions $sessions
    end

    set -l repos
    if test -d "$dev_dir"
        set repos (fd -t d -H --no-ignore --min-depth 2 --max-depth 4 '^\.git$' "$dev_dir" \
            | string replace -r '/\.git/?$' '' \
            | string replace "$HOME/" '')
    end
    test -d "$HOME/dotfiles/.git"; and set -a repos dotfiles
    if test (count $repos) -gt 0
        set repos (printf '%s\n' $repos | sort -u)
    end

    set -l tab (printf '\t')
    set -l choices
    for session in $sorted_sessions
        set -a choices (string join "$tab" session "$session")
    end
    for repo in $repos
        set -a choices (string join "$tab" repo "+ $repo")
    end
    if test (count $choices) -eq 0
        echo "No Zellij sessions or repositories found."
        return 1
    end

    set -l selected (printf '%s\n' $choices | fzf \
        --delimiter="$tab" \
        --with-nth=2.. \
        --layout=reverse-list \
        --border=rounded \
        --border-label=" Zellij Sessions " \
        --header="Enter: open | Esc: cancel" \
        --prompt="> " \
        --info=inline \
        --height=40%)
    set -l fzf_status $status
    test $fzf_status -eq 130; and return 0
    test $fzf_status -eq 0; or return $fzf_status
    test -n "$selected"; or return 0

    set -l selected_parts (string split -m 1 "$tab" -- "$selected")
    if test (count $selected_parts) -ne 2
        echo "error: invalid picker selection."
        return 1
    end
    set -l choice_type $selected_parts[1]
    set selected $selected_parts[2]

    mkdir -p (dirname "$history_file")

    if test "$choice_type" = repo
        set -l relative_dir (string replace '+ ' '' "$selected")
        set -l project_dir "$HOME/$relative_dir"
        set -l base (basename "$project_dir")
        set -l session "$base"
        set -l i 2
        set -l sessions (__zl_session_names)
        while contains -- "$session" $sessions
            set session "$base-$i"
            set i (math $i + 1)
        end
        echo "$session" >> "$history_file"
        __zl_open "$project_dir" "$session"
    else
        echo "$selected" >> "$history_file"
        __zl_attach "$selected"
    end
end

function __zl_confirm_sessions --argument-names action
    set -e argv[1]
    set -l sessions $argv
    set -l label (string join ', ' $sessions)
    read -P "$action Zellij session(s) '$label'? [y/N] " -l answer
    string match -qr '^[Yy]$' -- "$answer"
end

function __zl_stop
    set -l sessions $argv
    test (count $sessions) -gt 0; or set sessions (basename (pwd))

    __zl_confirm_sessions Stop $sessions; or begin
        echo "Cancelled."
        return 0
    end

    set -l failed 0
    for session in $sessions
        command zellij kill-session -- "$session"; or set failed 1
    end
    return $failed
end

function __zl_delete
    set -l sessions $argv
    test (count $sessions) -gt 0; or set sessions (basename (pwd))

    __zl_confirm_sessions Delete $sessions; or begin
        echo "Cancelled."
        return 0
    end

    set -l failed 0
    for session in $sessions
        command zellij delete-session -f -- "$session"; or set failed 1
    end
    return $failed
end

function __zl_help
    printf '%s\n' \
        'Usage: zl [PATH]' \
        '       zl <command> [args]' \
        '' \
        'Commands:' \
        '  open [PATH]         Open the project session (default: current directory)' \
        '  pick                Select a session or repository with fzf' \
        '  list                List Zellij sessions' \
        '  stop [SESSION...]   Stop sessions (default: current directory name)' \
        '  delete [SESSION...] Delete saved sessions (default: current directory name)' \
        '  help                Show this help'
end

function zl --description "Manage project sessions in Zellij"
    if test (count $argv) -gt 0; and contains -- $argv[1] help -h --help
        __zl_help
        return 0
    end

    if not command -q zellij
        echo "error: zellij command not found."
        return 127
    end

    if test (count $argv) -eq 0
        __zl_open (pwd)
        return $status
    end

    set -l subcommand $argv[1]
    set -e argv[1]

    switch "$subcommand"
        case open
            if test (count $argv) -gt 1
                echo "Usage: zl open [PATH]"
                return 2
            end
            set -l path (pwd)
            test (count $argv) -eq 0; or set path $argv[1]
            __zl_open "$path"
        case pick
            if test (count $argv) -gt 0
                echo "Usage: zl pick"
                return 2
            end
            __zl_pick
        case list ls
            if test (count $argv) -gt 0
                echo "Usage: zl list"
                return 2
            end
            __zl_list
        case stop
            __zl_stop $argv
        case delete rm
            __zl_delete $argv
        case help -h --help
            __zl_help
        case '*'
            if test -d "$subcommand"
                if test (count $argv) -gt 0
                    echo "Usage: zl [PATH]"
                    return 2
                end
                __zl_open "$subcommand"
            else
                echo "error: unknown command or directory: $subcommand"
                __zl_help
                return 2
            end
    end
end
