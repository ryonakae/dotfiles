function hermes --description "Run Hermes Agent through Agent Safehouse"
    if not command -q safehouse
        echo "error: safehouse command not found." >&2
        return 127
    end

    set -l safehouse_args (__safehouse_args)

    # Hermes 公式に runtime 識別 marker が無いため、skill (commit-push など) が
    # 「Hermes セッション内」と判別できるよう独自 marker を子プロセスへ伝搬する。
    set -fx HERMES_AGENT 1
    set -a safehouse_args --env-pass=HERMES_AGENT

    command safehouse $safehouse_args -- hermes $argv
    return $status
end
