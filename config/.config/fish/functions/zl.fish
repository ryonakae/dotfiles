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
    if zellij list-sessions --short 2>/dev/null | string match -q -x -- $session
        set session_exists 1
    end

    if test $session_exists -eq 0
        __zellij_apply_dev_desktop "$session" >/dev/null 2>&1 &
        disown
    end

    if test $session_exists -eq 1
        cd $project_dir && zellij attach "$session"
    else
        cd $project_dir && zellij -l dev attach -c $session
    end
    cd $orig_dir
end
