function hermes --description "Run Hermes through Agent Safehouse"
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

    # Hermes 専用 deny ルール
    set -l hermes_overrides "$HOME/.config/agent-safehouse/hermes-overrides.sb"
    if test -f "$hermes_overrides"
        set -a safehouse_args --append-profile="$hermes_overrides"
    end

    command safehouse $safehouse_args -- hermes $argv
    return $status
end
