function __hdr_session_names
    command herdr session list --json 2>/dev/null | command jq -r '.sessions[].name'
end

function __hdr_choices
    set -l dev_dir "$HOME/dev"
    set -l history_file "$HOME/.cache/hdr_history"
    set -l sessions_json (command herdr session list --json 2>/dev/null); or return
    set -l session_rows (printf '%s\n' "$sessions_json" | command jq -r \
        '.sessions[] | [.name, (if .running then "running" else "stopped" end)] | @tsv'); or return
    set -l sessions
    set -l sorted_sessions
    set -l tab (printf '\t')
    set -l records
    set -l label_width 0

    for row in $session_rows
        set -l fields (string split "$tab" -- "$row")
        set -a sessions $fields[1]
    end

    if test -f "$history_file" -a (count $sessions) -gt 0
        for name in (tail -r "$history_file" 2>/dev/null)
            if contains -- "$name" $sessions; and not contains -- "$name" $sorted_sessions
                set -a sorted_sessions "$name"
            end
        end
    end
    for name in $sessions
        contains -- "$name" $sorted_sessions; or set -a sorted_sessions "$name"
    end

    for session in $sorted_sessions
        set -l session_status stopped
        for row in $session_rows
            set -l fields (string split "$tab" -- "$row")
            if test "$fields[1]" = "$session"
                set session_status $fields[2]
                break
            end
        end
        set label_width (math max $label_width, (string length -- "$session"))
        set -a records (string join "$tab" session "$session" "$session_status" "$session")
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
    for repo in $repos
        set -a records (string join "$tab" repo "$repo" repository "+ $repo")
    end

    for record in $records
        set -l fields (string split "$tab" -- "$record")
        if test "$fields[1]" = session
            set -l status_color (set_color green)
            test "$fields[3]" = stopped; and set status_color (set_color red)
            set -l display_status (printf '%s%s%s' "$status_color" "$fields[3]" (set_color normal))
            printf '%s\t%s\t%s\t%-*s  %s\n' $fields[1] $fields[2] $fields[3] $label_width $fields[4] "$display_status"
        else
            printf '%s\t%s\t%s\t%s\n' $fields[1] $fields[2] $fields[3] $fields[4]
        end
    end
end

function __hdr_list
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

    set -l tab (printf '\t')
    set -l history_file "$HOME/.cache/hdr_history"

    while true
        set -l choices (__hdr_choices); or return
        if test (count $choices) -eq 0
            echo "No Herdr sessions or repositories found."
            return 1
        end

        set -l result (printf '%s\n' $choices | fzf \
            --delimiter="$tab" \
            --with-nth=4 \
            --ansi \
            --layout=reverse-list \
            --border=rounded \
            --border-label=" Herdr Sessions " \
            --header="Enter: open | Ctrl-S: stop session | Ctrl-D: delete session | Esc: cancel" \
            --prompt="> " \
            --info=inline \
            --height=60% \
            --expect=ctrl-s,ctrl-d)
        set -l fzf_status $status
        test $fzf_status -eq 130; and return 0
        test $fzf_status -eq 0; or return $fzf_status
        test (count $result) -ge 2; or return 0

        set -l action $result[1]
        test -n "$action"; or set action open
        set -l selected_parts (string split "$tab" -- "$result[2]")
        test (count $selected_parts) -ge 4; or begin
            echo "error: invalid picker selection."
            return 1
        end
        set -l choice_type $selected_parts[1]
        set -l target $selected_parts[2]

        if test "$choice_type" = repo
            test "$action" = open; or continue

            set -l project_dir "$HOME/$target"
            set -l base (__hdr_project_session_name "$project_dir")
            set -l session "$base"
            set -l i 2
            set -l sessions (__hdr_session_names)
            while contains -- "$session" $sessions
                set session "$base-$i"
                set i (math $i + 1)
            end
            __hdr_validate_session_name "$session"; or return
            mkdir -p (dirname "$history_file")
            echo "$session" >>"$history_file"
            __hdr_open "$project_dir" "$session"
            return $status
        end

        switch "$action"
            case ctrl-s
                __hdr_stop "$target"
            case ctrl-d
                __hdr_delete "$target"
            case open
                mkdir -p (dirname "$history_file")
                echo "$target" >>"$history_file"
                __hdr_attach "$target"
                return $status
        end
    end
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

function __hdr_project_session_name --argument-names project_dir
    set -l session (string replace -ar '[^A-Za-z0-9._-]+' '-' -- (basename "$project_dir"))
    set session (string replace -r '^-+' '' -- "$session")
    test -n "$session"; and echo "$session"; or echo session
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
    test -n "$session" || set session (__hdr_project_session_name "$project_dir")
    __hdr_validate_session_name "$session"; or return

    command env -C "$project_dir" herdr --session "$session"
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
    test (count $sessions) -gt 0; or set sessions (__hdr_project_session_name (pwd))

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
    test (count $sessions) -gt 0; or set sessions (__hdr_project_session_name (pwd))

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
        '  list                Select or manage sessions and repositories with fzf' \
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
