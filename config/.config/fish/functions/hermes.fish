function hermes --description "Run Hermes Agent through Agent Safehouse"
    if not command -q safehouse
        echo "error: safehouse command not found." >&2
        return 127
    end

    set -l safehouse_args (__safehouse_args)

    # rw
    set -a safehouse_args --add-dirs="$HOME/.hermes"
    set -a safehouse_args --add-dirs="$HOME/.local/state/hermes"
    set -a safehouse_args --add-dirs="$HOME/Dev/private"
    set -a safehouse_args --add-dirs="$HOME/dotfiles"

    # ro
    set -a safehouse_args --add-dirs-ro="$HOME/.local/bin"
    set -a safehouse_args --add-dirs-ro=/usr/local/bin
    set -a safehouse_args --add-dirs-ro="/Applications/Docker.app"
    set -a safehouse_args --add-dirs-ro="$HOME/.local/share/opencode"

    # Hermes Agent 専用 deny ルール
    set -l hermes_overrides "$HOME/.config/agent-safehouse/hermes-overrides.sb"
    if test -f "$hermes_overrides"
        set -a safehouse_args --append-profile="$hermes_overrides"
    end

    # agent-safehouse 内で Chrome の内側 sandbox 初期化が失敗するため、
    # Hermes から呼ぶ agent-browser にだけ Chrome 起動引数を渡す。
    # 実 Chrome プロファイル (cookie / 履歴 / 保存パスワード) と分離するため user-data-dir を強制する。
    set -fx AGENT_BROWSER_ARGS "--no-sandbox,--disable-gpu,--disable-dev-shm-usage,--user-data-dir=$HOME/.hermes/chrome-profile"

    # safehouse は既定で env を sanitize するため、TUI 起動フラグは --env-pass で明示的に通す。
    if test (count $argv) -eq 0
        set -a safehouse_args --env-pass=HERMES_TUI
        set -fx HERMES_TUI 1
    end

    command safehouse $safehouse_args -- hermes $argv
    return $status
end
