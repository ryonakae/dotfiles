function safe --description "Run a command through Agent Safehouse"
    if not test -x "/opt/homebrew/bin/safehouse"
        echo "error: safehouse command not found. Install it from https://agent-safehouse.dev/docs/getting-started" >&2
        return 127
    end

    # 起動タイミングによっては GUI セッションが root の TMPDIR を継承し、
    # safehouse のポリシー生成が mktemp で失敗する
    if not test -w "$TMPDIR"
        set -fx TMPDIR (getconf DARWIN_USER_TEMP_DIR)
    end

    set -l safehouse_args (__safehouse_args)
    or return $status

    command "$HOME/.config/agent-safehouse/run-with-agent-env.sh" "/opt/homebrew/bin/safehouse" $safehouse_args -- $argv
    return $status
end
