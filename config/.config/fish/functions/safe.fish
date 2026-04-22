function safe --description "Run a command through Agent Safehouse"
    if not command -q safehouse
        echo "error: safehouse command not found. Install it from https://agent-safehouse.dev/docs/getting-started" >&2
        return 127
    end

    set -l safehouse_args (__safehouse_args)

    command safehouse $safehouse_args -- $argv
    return $status
end
