## Safehouse の既定値をここで固定して、各 agent wrapper は起動コマンドだけを持つ。
function __safehouse_args --description "Build default Agent Safehouse arguments"
    set -l git_root (command git rev-parse --show-toplevel 2>/dev/null)
    set -l workdir

    if test -n "$git_root"
        set workdir (path resolve "$git_root")
    else
        set workdir (pwd -P)
    end

    set -l dotfiles_dir "$HOME/dotfiles"
    set -l overrides "$HOME/.config/agent-safehouse/local-overrides.sb"

    # shell で export 済みの値は既定では落ちるので、必要な秘密と非機密の挙動制御だけを明示的に通す。
    # SSH_AUTH_SOCK は git push 等で ssh-agent (Keychain 経由) を使うために必要。
    # terminal-notifier（Cocoa アプリ）が macOS 通知センターと通信するための Mach サービスを許可。
    set -l args \
        --workdir="$workdir" \
        --env-pass=CONTEXT7_API_KEY \
        --env-pass=DISABLE_AUTOUPDATER \
        --env-pass=NO_BROWSER \
        --env-pass=TERM_PROGRAM \
        --env-pass=AGENT_BROWSER_ARGS \
        --env-pass=AGENT_BROWSER_PROFILE \
        --env-pass=SSH_AUTH_SOCK \
        --enable=macos-gui,ssh,cleanshot,agent-browser,docker,clipboard

    # dotfiles 配下への symlink を他 repo からでも辿れるように、常時 read-only で足す。
    if test -d "$dotfiles_dir"
        set -a args --add-dirs-ro="$dotfiles_dir"
    end

    # 機密 deny は固定ルールとして .sb 側に寄せ、wrapper では読み込み順だけを管理する。
    if test -f "$overrides"
        set -a args --append-profile="$overrides"
    end

    printf '%s\n' $args
end
