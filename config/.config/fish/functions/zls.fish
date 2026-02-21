function zls -d "Zellijのセッションをfzfで選択してアタッチ"
    set -l sessions (zellij list-sessions --short 2>/dev/null)

    if test -z "$sessions"
        echo "アクティブなZellijセッションがありません。"
        return 1
    end

    set -l selected (string join \n $sessions | fzf \
        --layout=reverse-list \
        --border=rounded \
        --border-label=" Zellij Sessions " \
        --header="↑↓: 移動, Enter: 決定, Esc: キャンセル" \
        --prompt="> " \
        --info=inline \
        --height=40%)

    if test -n "$selected"
        zellij attach "$selected"
    end
end
