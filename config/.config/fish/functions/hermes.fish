function hermes --description "Run Hermes Agent through Agent Safehouse"
    if not command -q safehouse
        echo "error: safehouse command not found." >&2
        return 127
    end

    set -l safehouse_args (__safehouse_args)

    command safehouse $safehouse_args -- hermes $argv
    return $status
end
