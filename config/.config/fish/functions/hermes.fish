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

    # Hermes Agent 専用オーバーライド
    set -l hermes_overrides "$HOME/.config/agent-safehouse/hermes-overrides.sb"
    if test -f "$hermes_overrides"
        set -a safehouse_args --append-profile="$hermes_overrides"
    end

    # agent-safehouse 内で Chrome の内側 sandbox 初期化が失敗するため、
    # Hermes から呼ぶ agent-browser にだけ Chrome 起動引数を渡す。
    # 実 Chrome プロファイル (cookie / 履歴 / 保存パスワード) と分離するため、
    # agent-browser の正規オプションで専用 profile directory を指定する。
    set -fx AGENT_BROWSER_ARGS "--no-sandbox,--disable-gpu,--disable-dev-shm-usage"
    set -fx AGENT_BROWSER_PROFILE "$HOME/.hermes/chrome-profile"

    # uv/pip の既定 cache (~/.cache 配下) は sandbox の write deny に引っ掛かるため、
    # rw 全面許可されている ~/.hermes 配下に隔離する。
    set -fx UV_CACHE_DIR "$HOME/.hermes/cache/uv"
    set -fx PIP_CACHE_DIR "$HOME/.hermes/cache/pip"
    set -a safehouse_args --env-pass=UV_CACHE_DIR --env-pass=PIP_CACHE_DIR

    command safehouse $safehouse_args -- hermes $argv
    return $status
end
