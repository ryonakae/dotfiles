function hermes --description "Run Hermes Agent through Agent Safehouse"
    if not test -x "/opt/homebrew/bin/safehouse"
        echo "error: safehouse command not found." >&2
        return 127
    end

    # 別ユーザー用の TMPDIR を継承しても Safehouse の mktemp を失敗させない。
    if not test -d "$TMPDIR"; or not test -w "$TMPDIR"; or not test -x "$TMPDIR"
        set -fx TMPDIR (command getconf DARWIN_USER_TEMP_DIR)
        if not test -d "$TMPDIR"; or not test -w "$TMPDIR"; or not test -x "$TMPDIR"
            echo "error: no usable user temporary directory." >&2
            return 1
        end
    end

    set -l safehouse_args (__safehouse_args)
    or return $status

    command "$HOME/.config/agent-safehouse/run-with-agent-env.sh" "/opt/homebrew/bin/safehouse" $safehouse_args -- "$HOME/.local/libexec/hermes" $argv
    return $status
end
