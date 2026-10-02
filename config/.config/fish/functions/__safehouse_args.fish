function __safehouse_args --description "Build default Agent Safehouse arguments"
    set -l git_root (command git rev-parse --show-toplevel 2>/dev/null)
    set -l workdir
    if test -n "$git_root"
        set workdir (path resolve "$git_root")
    else
        set workdir (pwd -P)
    end

    # シェル履歴へエージェントのコマンドを残さない。
    set -fx HISTFILE /dev/null

    set -l args \
        --workdir="$workdir" \
        --env \
        --add-dirs="$HOME" \
        --enable=macos-gui,ssh,cleanshot,agent-browser,docker,clipboard,all-agents,wide-read,keychain,xcode,process-control,launch-services

    # HOME の許可より後に拒否を適用し、保護ファイルの欠落を黙って許可にしない。
    for profile in compatibility local-overrides
        set -l file "$HOME/.config/agent-safehouse/$profile.sb"
        if not test -r "$file"
            echo "error: required Safehouse profile is missing: $file" >&2
            return 1
        end
        set -a args --append-profile="$file"
    end

    printf '%s\n' $args
end
