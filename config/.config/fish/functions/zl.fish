function zl --description "Open a Zellij session for a project"
    set -l project_dir
    if test (count $argv) -ge 1
        set project_dir (realpath $argv[1])
    else
        set project_dir (pwd)
    end
    set -l session (basename $project_dir)
    set -l orig_dir (pwd)
    set -l session_exists 0
    set -l sessions (zellij list-sessions --short 2>/dev/null)
    if contains -- $session $sessions
        set session_exists 1
    end

    if set -q ZELLIJ
        # zellij セッション内: 二重起動を避けて切り替える
        if test $session_exists -eq 1
            zellij action switch-session $session
        else
            zellij action switch-session -l dev -c $project_dir $session
        end
    else
        if test $session_exists -eq 1
            cd $project_dir && zellij attach "$session"
        else
            cd $project_dir && zellij -l dev attach -c $session
        end
        cd $orig_dir
    end
end
