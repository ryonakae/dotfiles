function __zl_session_names
    command zellij list-sessions --short 2>/dev/null
end

function __zl_choices
    set -l dev_dir "$HOME/dev"
    set -l history_file "$HOME/.cache/zl_history"
    set -l sessions (command zellij list-sessions --short 2>/dev/null)
    set -l session_rows (command zellij list-sessions --no-formatting 2>/dev/null)
    set -l sorted_sessions
    set -l tab (printf '\t')
    set -l records
    set -l label_width 0

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
        set -l session_status running
        set -l escaped_session (string escape --style=regex -- "$session")
        set -l row_pattern '^'$escaped_session' \[Created [0-9]+[A-Za-z]+( [0-9]+[A-Za-z]+)* ago\]( \(EXITED - attach to resurrect\))?$'
        for row in $session_rows
            if string match -qr -- "$row_pattern" "$row"
                string match -qr '\] \(EXITED - attach to resurrect\)$' -- "$row"; and set session_status stopped
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

function __zl_list
    if not command -q fd
        echo "error: fd command not found. Install it with: brew install fd"
        return 127
    end
    if not command -q fzf
        echo "error: fzf command not found. Install it with: brew install fzf"
        return 127
    end

    set -l tab (printf '\t')
    set -l history_file "$HOME/.cache/zl_history"

    while true
        set -l choices (__zl_choices); or return
        if test (count $choices) -eq 0
            echo "No Zellij sessions or repositories found."
            return 1
        end

        set -l result (printf '%s\n' $choices | fzf \
            --delimiter="$tab" \
            --with-nth=4 \
            --ansi \
            --layout=reverse-list \
            --border=rounded \
            --border-label=" Zellij Sessions " \
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
        set -l session_status $selected_parts[3]

        if test "$choice_type" = repo
            test "$action" = open; or continue

            set -l project_dir "$HOME/$target"
            set -l base (basename "$project_dir")
            set -l session "$base"
            set -l i 2
            set -l sessions (__zl_session_names)
            while contains -- "$session" $sessions
                set session "$base-$i"
                set i (math $i + 1)
            end
            mkdir -p (dirname "$history_file")
            echo "$session" >>"$history_file"
            __zl_open "$project_dir" "$session"
            return $status
        end

        switch "$action"
            case ctrl-s
                if test "$session_status" = stopped
                    echo "Zellij session '$target' is already stopped."
                else
                    __zl_stop "$target"
                end
            case ctrl-d
                __zl_delete "$target"
            case open
                mkdir -p (dirname "$history_file")
                echo "$target" >>"$history_file"
                __zl_attach "$target"
                return $status
        end
    end
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
        '  list                Select or manage sessions and repositories with fzf' \
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
