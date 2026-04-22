function hermes --description "Run Hermes through Agent Safehouse"
    if not command -q safehouse
        echo "error: safehouse command not found." >&2
        return 127
    end

    set -l safehouse_args (__safehouse_args)
    set -a safehouse_args --add-dirs="$HOME/.hermes"
    set -a safehouse_args --add-dirs-ro="$HOME/.local/bin"
    set -a safehouse_args --add-dirs="$HOME/.local/state/hermes"
    set -a safehouse_args --add-dirs-ro=/usr/local/bin
    set -a safehouse_args --add-dirs-ro="/Applications/Docker.app"
    set -a safehouse_args --add-dirs="$HOME/Library/LaunchAgents"

    command safehouse $safehouse_args -- hermes $argv
    return $status
end
