function zls -d "~/devのリポジトリを選択してZellijセッションを作成/アタッチ"
    set -l dev_dir $HOME/dev
    set -l history_file $HOME/.cache/zls_history

    # 既存セッション一覧を取得
    set -l sessions (zellij list-sessions --short 2>/dev/null)

    # 履歴ファイルを元に既存セッションを最近選択した順にソート
    set -l sorted_sessions
    if test -f $history_file -a -n "$sessions"
        for name in (tail -r $history_file 2>/dev/null)
            if contains -- $name $sessions && not contains -- $name $sorted_sessions
                set sorted_sessions $sorted_sessions $name
            end
        end
        for name in $sessions
            contains -- $name $sorted_sessions || set sorted_sessions $sorted_sessions $name
        end
    else
        set sorted_sessions $sessions
    end

    # グロブで深度1〜3の.gitを直接マッチ（findより大幅に高速、OS依存なし）
    set -l repos
    for gitdir in $dev_dir/*/.git $dev_dir/*/*/.git $dev_dir/*/*/*/.git
        test -d "$gitdir" && set repos $repos (string replace "$dev_dir/" "" (string replace "/.git" "" $gitdir))
    end
    set repos (printf '%s\n' $repos | sort | string replace -r '^' '+ ')

    if test -z "$sorted_sessions" -a -z "$repos"
        echo "No sessions or repositories found."
        return 1
    end

    set -l choices
    test -n "$sorted_sessions" && set choices $sorted_sessions
    test -n "$repos" && set choices $choices $repos

    # reload 用にリポジトリ一覧をテンプファイルに書き出す
    set -l repos_file (mktemp)
    string join \n $repos > $repos_file

    set -l selected (string join \n $choices | fzf \
        --layout=reverse-list \
        --border=rounded \
        --border-label=" Zellij Sessions " \
        --header="Enter: attach | Ctrl-D: delete | Ctrl-K: kill | Ctrl-R: reload | Esc: cancel" \
        --prompt="> " \
        --info=inline \
        --height=40% \
        --bind "ctrl-d:execute-silent([[ ! {} =~ ^'+ ' ]] && zellij delete-session {})+reload(zellij list-sessions --short 2>/dev/null; cat $repos_file)" \
        --bind "ctrl-k:execute-silent([[ ! {} =~ ^'+ ' ]] && zellij kill-session {})+reload(zellij list-sessions --short 2>/dev/null; cat $repos_file)" \
        --bind "ctrl-r:reload(zellij list-sessions --short 2>/dev/null; cat $repos_file)")

    rm -f $repos_file
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
        mkdir -p (dirname $history_file)
        echo $session >> $history_file
        cd "$dev_dir/$dir"
        zellij -l dev attach -c $session
    else
        # 既存セッションにアタッチ
        mkdir -p (dirname $history_file)
        echo $selected >> $history_file
        zellij attach "$selected"
    end
end
