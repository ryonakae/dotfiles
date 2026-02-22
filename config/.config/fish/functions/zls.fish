function zls -d "~/devのリポジトリを選択してZellijセッションを作成/アタッチ"
    set -l dev_dir $HOME/dev

    # 既存セッション一覧
    set -l sessions (zellij list-sessions --short 2>/dev/null)

    # グロブで深度1〜3の.gitを直接マッチ（findより大幅に高速、OS依存なし）
    set -l repos
    for gitdir in $dev_dir/*/.git $dev_dir/*/*/.git $dev_dir/*/*/*/.git
        test -d "$gitdir" && set repos $repos (string replace "$dev_dir/" "" (string replace "/.git" "" $gitdir))
    end
    set repos (printf '%s\n' $repos | sort | string replace -r '^' '+ ')

    if test -z "$sessions" -a -z "$repos"
        echo "セッションもリポジトリも見つかりませんでした。"
        return 1
    end

    # 既存セッション + リポジトリ一覧を結合してfzfに渡す
    set -l choices
    if test -n "$sessions"
        set choices $sessions
    end
    if test -n "$repos"
        set choices $choices $repos
    end

    set -l selected (string join \n $choices | fzf \
        --layout=reverse-list \
        --border=rounded \
        --border-label=" Zellij Sessions " \
        --header="既存セッション または + リポジトリを選択 | Esc: キャンセル" \
        --prompt="> " \
        --info=inline \
        --height=40%)

    test -z "$selected" && return

    if string match -q '+ *' $selected
        # 新規セッション: ディレクトリに移動してセッション作成
        set -l dir (string replace '+ ' '' $selected)
        set -l base (basename $dir)
        set -l session $base
        set -l i 2
        while zellij list-sessions --short 2>/dev/null | string match -q $session
            set session "$base-$i"
            set i (math $i + 1)
        end
        cd "$dev_dir/$dir"
        zellij attach -c "$session"
    else
        # 既存セッションにアタッチ
        zellij attach "$selected"
    end
end
