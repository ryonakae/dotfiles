function __hdr_session_names
    command herdr session list --json 2>/dev/null | command jq -r '.sessions[].name'
end

function __hdr_list
    if not command -q jq
        echo "error: jq command not found. Install it with: brew install jq"
        return 127
    end

    set -l sessions_json (command herdr session list --json); or return
    set -l running_status running
    set -l stopped_status stopped
    if test -t 1
        set running_status (printf '%s%s%s' (set_color green) running (set_color normal))
        set stopped_status (printf '%s%s%s' (set_color red) stopped (set_color normal))
    end
    set -l rows (printf '%s\n' "$sessions_json" | command jq -r \
        --arg running "$running_status" \
        --arg stopped "$stopped_status" \
        '.sessions[] | [.name, (if .running then $running else $stopped end)] | @tsv'); or return
    set -l tab (printf '\t')
    printf '%s\n' (string join "$tab" name status) $rows | command column -t -s "$tab"
end

function __hdr_session_running --argument-names session
    command herdr session list --json 2>/dev/null \
        | command jq -r --arg name "$session" '.sessions[] | select(.name == $name) | .running'
end

function __hdr_require_outer_shell
    if test "$HERDR_ENV" = 1
        echo "error: detach from Herdr before opening or modifying a session."
        return 1
    end
end

function __hdr_validate_session_name --argument-names session
    if string match -qr '^[A-Za-z0-9._][A-Za-z0-9._-]*$' -- "$session"
        return 0
    end

    echo "error: '$session' is not a valid Herdr session name."
    echo "Session names must start with an ASCII letter, number, '.', or '_',"
    echo "and may also contain '-'."
    return 2
end

function __hdr_attach --argument-names session
    __hdr_require_outer_shell; or return
    __hdr_validate_session_name "$session"; or return
    command herdr session attach "$session"
end

function __hdr_open --argument-names path session
    __hdr_require_outer_shell; or return

    if not test -d "$path"
        echo "error: directory not found: $path"
        return 1
    end

    set -l project_dir (realpath "$path")
    test -n "$session" || set session (basename "$project_dir")
    __hdr_validate_session_name "$session"; or return

    command env -C "$project_dir" herdr --session "$session"
end

function __hdr_pick
    __hdr_require_outer_shell; or return

    if not command -q fd
        echo "error: fd command not found. Install it with: brew install fd"
        return 127
    end
    if not command -q fzf
        echo "error: fzf command not found. Install it with: brew install fzf"
        return 127
    end
    if not command -q jq
        echo "error: jq command not found. Install it with: brew install jq"
        return 127
    end

    set -l dev_dir "$HOME/dev"
    set -l history_file "$HOME/.cache/hdr_history"
    set -l sessions (__hdr_session_names)
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
        set repos (printf '%s\n' $repos | sort -u | string replace -r '^' '+ ')
    end

    set -l choices $sorted_sessions $repos
    if test (count $choices) -eq 0
        echo "No Herdr sessions or repositories found."
        return 1
    end

    set -l selected (printf '%s\n' $choices | fzf \
        --layout=reverse-list \
        --border=rounded \
        --border-label=" Herdr Sessions " \
        --header="Enter: open | Esc: cancel" \
        --prompt="> " \
        --info=inline \
        --height=40%)
    set -l fzf_status $status
    test $fzf_status -eq 130; and return 0
    test $fzf_status -eq 0; or return $fzf_status
    test -n "$selected"; or return 0

    mkdir -p (dirname "$history_file")

    if string match -q '+ *' "$selected"
        set -l relative_dir (string replace '+ ' '' "$selected")
        set -l project_dir "$HOME/$relative_dir"
        set -l base (basename "$project_dir")
        set -l session "$base"
        set -l i 2
        set -l sessions (__hdr_session_names)
        while contains -- "$session" $sessions
            set session "$base-$i"
            set i (math $i + 1)
        end
        echo "$session" >> "$history_file"
        __hdr_open "$project_dir" "$session"
    else
        echo "$selected" >> "$history_file"
        __hdr_attach "$selected"
    end
end

function __hdr_confirm_sessions --argument-names action
    set -e argv[1]
    set -l sessions $argv
    set -l label (string join ', ' $sessions)
    read -P "$action Herdr session(s) '$label'? [y/N] " -l answer
    string match -qr '^[Yy]$' -- "$answer"
end

function __hdr_stop
    __hdr_require_outer_shell; or return

    if not command -q jq
        echo "error: jq command not found. Install it with: brew install jq"
        return 127
    end

    set -l sessions $argv
    test (count $sessions) -gt 0; or set sessions (basename (pwd))

    __hdr_confirm_sessions Stop $sessions; or begin
        echo "Cancelled."
        return 0
    end

    set -l failed 0
    for session in $sessions
        if not __hdr_validate_session_name "$session"
            set failed 1
            continue
        end

        set -l running (__hdr_session_running "$session")
        switch "$running"
            case true
                command herdr session stop "$session"; or set failed 1
            case false
                echo "Herdr session '$session' is already stopped."
            case '*'
                echo "No Herdr session found for '$session'."
                set failed 1
        end
    end
    return $failed
end

function __hdr_delete
    __hdr_require_outer_shell; or return

    if not command -q jq
        echo "error: jq command not found. Install it with: brew install jq"
        return 127
    end

    set -l sessions $argv
    test (count $sessions) -gt 0; or set sessions (basename (pwd))

    __hdr_confirm_sessions Delete $sessions; or begin
        echo "Cancelled."
        return 0
    end

    set -l failed 0
    for session in $sessions
        if not __hdr_validate_session_name "$session"
            set failed 1
            continue
        end

        set -l running (__hdr_session_running "$session")
        switch "$running"
            case true
                command herdr session stop "$session"; and command herdr session delete "$session"
                or set failed 1
            case false
                command herdr session delete "$session"; or set failed 1
            case '*'
                echo "No Herdr session found for '$session'."
                set failed 1
        end
    end
    return $failed
end

function __hdr_help
    printf '%s\n' \
        'Usage: hdr [PATH]' \
        '       hdr <command> [args]' \
        '' \
        'Commands:' \
        '  open [PATH]         Open the project session (default: current directory)' \
        '  pick                Select a session or repository with fzf' \
        '  list                List Herdr sessions' \
        '  stop [SESSION...]   Stop sessions (default: current directory name)' \
        '  delete [SESSION...] Delete saved sessions (default: current directory name)' \
        '  help                Show this help'
end

function hdr --description "Manage project sessions in Herdr"
    if test (count $argv) -gt 0; and contains -- $argv[1] help -h --help
        __hdr_help
        return 0
    end

    if not command -q herdr
        echo "error: herdr command not found."
        return 127
    end

    if test (count $argv) -eq 0
        __hdr_open (pwd)
        return $status
    end

    set -l subcommand $argv[1]
    set -e argv[1]

    switch "$subcommand"
        case open
            if test (count $argv) -gt 1
                echo "Usage: hdr open [PATH]"
                return 2
            end
            set -l path (pwd)
            test (count $argv) -eq 0; or set path $argv[1]
            __hdr_open "$path"
        case pick
            if test (count $argv) -gt 0
                echo "Usage: hdr pick"
                return 2
            end
            __hdr_pick
        case list ls
            if test (count $argv) -gt 0
                echo "Usage: hdr list"
                return 2
            end
            __hdr_list
        case stop
            __hdr_stop $argv
        case delete rm
            __hdr_delete $argv
        case help -h --help
            __hdr_help
        case '*'
            if test -d "$subcommand"
                if test (count $argv) -gt 0
                    echo "Usage: hdr [PATH]"
                    return 2
                end
                __hdr_open "$subcommand"
            else
                echo "error: unknown command or directory: $subcommand"
                __hdr_help
                return 2
            end
    end
end
