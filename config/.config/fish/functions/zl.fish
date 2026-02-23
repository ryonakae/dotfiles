function zl --description "Start zellij session"
    set -l project_dir
    if test (count $argv) -ge 1
        set project_dir (realpath $argv[1])
    else
        set project_dir (pwd)
    end
    set -l session (basename $project_dir)
    cd $project_dir && zellij -l dev attach -c $session
end
