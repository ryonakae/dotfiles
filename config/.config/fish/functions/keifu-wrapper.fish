function keifu-wrapper --description "Run Keifu with a Git status pane title"
    # バックグラウンドでペインタイトルを5秒ごとに更新
    # OSC 0 でZellijがペインタイトルとして認識する
    fish -c '
        while true
            set -l branch (git symbolic-ref --short HEAD 2>/dev/null)
            if test -z "$branch"
                set branch (git rev-parse --short HEAD 2>/dev/null)
            end
            if test -z "$branch"
                set branch unknown
            end

            # keifuと同じ方式: staged + unstaged を個別に合算
            # git diff HEAD（ネット差分）では MM 状態ファイルの中間変更が消えて数値がずれるため
            set -l cached_lines (git diff --cached --numstat 2>/dev/null)
            set -l working_lines (git diff --numstat 2>/dev/null)

            set -l all_files
            set -l ins 0
            set -l del 0

            for line in $cached_lines $working_lines
                set -l parts (string split \t -- $line)
                # バイナリファイルは "- - filename" 形式なのでスキップ
                if test (count $parts) -ge 3; and test $parts[1] != "-"
                    set ins (math $ins + $parts[1])
                    set del (math $del + $parts[2])
                    if not contains -- $parts[3] $all_files
                        set -a all_files $parts[3]
                    end
                end
            end

            set -l files (count $all_files)

            if test $files -gt 0
                printf "\e]0;keifu: ⎇ %s (+%s,-%s)\a" $branch $ins $del
            else
                printf "\e]0;keifu: ⎇ %s\a" $branch
            end

            sleep 5
        end
    ' &
    set -l updater_pid $last_pid

    command keifu

    kill $updater_pid 2>/dev/null
end
