## Safehouse の既定値をここで固定して、各 agent wrapper は起動コマンドだけを持つ。
function __safehouse_args --description "Build default Agent Safehouse arguments"
    set -l git_root (command git rev-parse --show-toplevel 2>/dev/null)
    set -l workdir

    if test -n "$git_root"
        set workdir (path resolve "$git_root")
    else
        set workdir (pwd -P)
    end

    set -l overrides "$HOME/.config/agent-safehouse/local-overrides.sb"

    # シェル履歴汚染を抑制 (~/.zsh_history などへの書き込み denied 警告も同時に消える)。
    set -fx HISTFILE /dev/null

    # shell で export 済みの値は既定では落ちるので、必要な秘密と非機密の挙動制御だけを明示的に通す。
    # SSH_AUTH_SOCK は git push 等で ssh-agent (Keychain 経由) を使うために必要。
    # terminal-notifier (Cocoa アプリ) が macOS 通知センターと通信するための Mach サービスを許可。
    set -l args \
        --workdir="$workdir" \
        --env-pass=CONTEXT7_API_KEY \
        --env-pass=DISABLE_AUTOUPDATER \
        --env-pass=NO_BROWSER \
        --env-pass=TERM_PROGRAM \
        --env-pass=AGENT_BROWSER_ARGS \
        --env-pass=AGENT_BROWSER_PROFILE \
        --env-pass=SSH_AUTH_SOCK \
        --env-pass=HISTFILE \
        --enable=macos-gui,ssh,cleanshot,agent-browser,docker,clipboard,all-agents,wide-read,keychain,xcode

    # cwd 外の頻出 path を rw で開ける。--add-dirs=$HOME だと safehouse 既定の
    # ~/.ssh deny 等を後勝ちで上書きしてしまうので、top-level ごとに列挙する。
    # safehouse の 30-toolchains / all-agents で既に rw されている path (~/.bun, ~/.claude 等) は重複指定しない。
    # ~/Library は丸ごと開けると Cookies / Mail / Messages / ブラウザ profile が露出するため、
    # ~/Library/Caches だけ開けて他は default-deny に任せる。
    # ~/.hermes は信頼境界として deny を貫通させるため local-overrides.sb の allow 側に書く。
    for dir in \
        "$HOME/.com.moomoo.OpenD" \
        "$HOME/.config" \
        "$HOME/.local" \
        "$HOME/.cache" \
        "$HOME/.shepherd" \
        "$HOME/Library/Caches" \
        "$HOME/dotfiles"
        if test -d "$dir"
            set -a args --add-dirs="$dir"
        end
    end

    # 作業 repo 親 dir はマシンによって無い場合がある。
    if test -d "$HOME/Dev"
        set -a args --add-dirs="$HOME/Dev"
    end

    # 機密 deny は固定ルールとして .sb 側に寄せ、wrapper では読み込み順だけを管理する。
    if test -f "$overrides"
        set -a args --append-profile="$overrides"
    end

    printf '%s\n' $args
end
