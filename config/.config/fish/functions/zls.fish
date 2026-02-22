function zls -d "~/devのリポジトリを選択してZellijセッションを作成/アタッチ"
    set -l dev_dir $HOME/dev

    # 既存セッション一覧
    set -l sessions (zellij list-sessions --short 2>/dev/null)

    # ~/dev以下のgitリポジトリを相対パスで取得し、+ プレフィックスを付ける
    # node_modules等の重いディレクトリはpruneでスキップして高速化
    set -l repos (find $dev_dir -maxdepth 5 \
        \( -name "node_modules" -o -name "vendor" -o -name ".cache" -o -name "target" -o -name "dist" -o -name "build" -o -name ".next" \) -prune \
        -o -name ".git" -type d -print 2>/dev/null \
        | string replace -r '/.git$' '' \
        | string replace "$dev_dir/" "" \
        | sort \
        | string replace -r '^' '+ ')

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
        --header="既存セッション または + リポジトリを選択" \
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
