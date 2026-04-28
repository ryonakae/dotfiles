# mosh/ssh 経由の非 Aqua シェルには launchd の SSH_AUTH_SOCK が降りてこないため、
# GUI セッションが持っている socket パスを引っ張ってくる。直接ログイン時には既に
# 設定済みなので、`set -q` ガードで触らない。
if not set -q SSH_AUTH_SOCK
    set -l sock (launchctl asuser (id -u) launchctl getenv SSH_AUTH_SOCK 2>/dev/null)
    # launchd の env に SSH_AUTH_SOCK が登録されないケースでは、ssh-agent の
    # socket 自体を /private/tmp 配下から直接拾うフォールバックを使う。
    if test -z "$sock" -o ! -S "$sock"
        set sock (find /private/tmp -maxdepth 2 -name Listeners -type s -user (id -u) 2>/dev/null | head -n 1)
    end
    if test -n "$sock" -a -S "$sock"
        set -gx SSH_AUTH_SOCK $sock
    end
end
