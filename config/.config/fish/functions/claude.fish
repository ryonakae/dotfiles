function claude --description "Run Claude through Agent Safehouse"
    set -l mcp_args --mcp-config "$HOME/.claude/mcp.json"
    set -l args
    # The variadic option must follow the prompt or precede the option terminator.
    for arg in $argv
        if test "$arg" = --
            set -a args $mcp_args
            set mcp_args
        end
        set -a args "$arg"
    end
    safe claude $args $mcp_args
end
